import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import UniverSheet from './ExcelViewer/UniverSheet.tsx';
import ChatPanel, { type Message } from './ChatPanel/ChatPanel.tsx'; // Import new component and type
import { type IWorkbookData } from '@univerjs/core';
import './App.css';

function App() {
  const [workbookData, setWorkbookData] = useState<IWorkbookData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [isBpssProcessing, setIsBpssProcessing] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  const jsonWorker = useRef<Worker | null>(null);


  // --- WebSocket Connection ---
  useEffect(() => {
    jsonWorker.current = new Worker('/json-stringifier.worker.js');
    console.log("JSON Stringifier Web Worker initialized.");

    // This is where we receive the stringified JSON back from the worker
    jsonWorker.current.onmessage = (event) => {
      const jsonString = event.data;
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(jsonString);
      }
    };

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws`;
    console.log(`Connecting WebSocket to: ${wsUrl}`);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setIsWsConnected(true);
    };

    // Handle incoming messages from the WebSocket
    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Message from server:', message);

        switch (message.type) {
          case 'chat_message':
            setMessages(prev => [...prev, message.payload as Message]);
            break;

          case 'workbook_update':
            setWorkbookData(message.payload as IWorkbookData);
            break;

          case 'notification':
            console.log(`Notification: [${message.payload.level}] ${message.payload.message}`);
            break;

          default:
            console.warn('Received unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', event.data, error);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsWsConnected(false);
      setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'System: Connection to server lost. Please refresh the page.',
          timestamp: new Date().toISOString(),
          error: true,
      }]);
    };

    ws.current.onerror = (err) => {
        console.error('WebSocket error:', err);
    };

    return () => {
      // Terminate the worker and close the WebSocket
      jsonWorker.current?.terminate();
      ws.current?.close();
    };
  }, []);

  // --- File Upload Handler ---
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Add the user message to chat immediately
    setMessages(prev => [...prev, {
        role: 'user',
        content: `Uploading file: ${file.name}`,
        timestamp: new Date().toISOString(),
    }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<IWorkbookData>('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setWorkbookData(response.data);

    } catch (error: any) {
      console.error('Error uploading file:', error);
    }
  };

  const handleProcessBpss = useCallback(async (formData: FormData) => {
    setIsBpssProcessing(true);
    setMessages(prev => [...prev, {
      role: 'user',
      content: 'Lancement du traitement BPSS avec 3 fichiers...',
      timestamp: new Date().toISOString(),
    }]);

    try {
        await axios.post('/bpss/process', formData, { // <-- NEW
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } catch (error: any) {
      console.error('Error processing BPSS files:', error);
      const errorMessage = error.response?.data?.detail || 'An unknown error occurred.';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Erreur lors du traitement BPSS : ${errorMessage}`,
        timestamp: new Date().toISOString(),
        error: true,
      }]);
    } finally {
      setIsBpssProcessing(false);
    }
  }, []);

  // --- Chat Message Sender ---
  const handleSendMessage = useCallback((messageText: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      // Add user's message to the chat UI immediately
      const userMessage: Message = {
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Send the message to the backend
      const wsMessage = {
          type: 'user_message',
          payload: { content: messageText }
      };
      ws.current.send(JSON.stringify(wsMessage));

    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Cannot send message. Not connected to the server.',
        timestamp: new Date().toISOString(),
        error: true,
      }]);
    }
  }, []);

  // --- Cell Change Handler ---
  const handleCellChange = useCallback(async (changeData: any) => {
    if (isWsConnected && ws.current && jsonWorker.current) {
        const wsMessage = {
            type: 'cell_update',
            payload: changeData
        };
      jsonWorker.current.postMessage(wsMessage);
    } else {
      if (!isWsConnected) console.warn('WebSocket is not connected.');
      if (!jsonWorker.current) console.warn('JSON worker is not available.');
    }
  }, [isWsConnected]);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>BudgiBot UI</h1>
        <p>A modern UI with FastAPI, React, and UniverJS</p>
      </header>

      <main className="main-content">
        <div className="layout-grid">

          {/* --- Left Panel: Chat & Controls --- */}
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            onProcessBpss={handleProcessBpss}
            isBpssProcessing={isBpssProcessing}
          />

          {/* --- Right Panel: Excel Component --- */}
          <div className="panel excel-panel">
            <h2>Excel Viewer</h2>
            {workbookData ? (
              <UniverSheet
                initialData={workbookData}
                onCellChange={handleCellChange}
                height={700}
              />
            ) : (
              <div className="placeholder">
                <p>Upload an Excel file to see it here.</p>
                {!isWsConnected && <p style={{color: 'red'}}>Connecting to server...</p>}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;