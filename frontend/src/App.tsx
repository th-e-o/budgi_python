import React, {useState, useEffect, useRef, useCallback} from 'react';
import axios from 'axios';
import UniverSheet, {type UniverSheetHandle} from './ExcelViewer/UniverSheet.tsx';
import ChatPanel from './ChatPanel/ChatPanel.tsx';
import {type IWorkbookData} from '@univerjs/core';
import Cookies from 'js-cookie';
import './App.css';
import type {ChatMessage, ServerMsg} from './Shared/Contract.tsx';
import {useWorkbook} from "./ExcelViewer/WorkbookContext.tsx";
import {blobToText} from "./Helpers/blobToText.tsx";
import UpdatesModal from "./Components/UpdatesModal.tsx";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
console.log(`Configuring API calls to: '${API_BASE_URL}'`);

axios.defaults.withCredentials = true;
axios.defaults.baseURL =
    API_BASE_URL && API_BASE_URL !== ''
        ? API_BASE_URL
        : `${window.location.protocol}//${window.location.host}`;

function App() {
    const {state, dispatch} = useWorkbook(); // <- global workbook
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isWsConnected, setIsWsConnected] = useState(false);
    const [isBpssProcessing, setIsBpssProcessing] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(
        Cookies.get('session_id') || null,
    );

    const ws = useRef<WebSocket | null>(null);
    const jsonWorker = useRef<Worker | null>(null);
    const sheetRef = useRef<UniverSheetHandle | null>(null);

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

        let wsUrl;
        if (API_BASE_URL) {
            // Development: Use the API base URL but switch protocol to ws/wss
            const wsHost = API_BASE_URL.replace(/^http/, 'ws');
            wsUrl = `${wsHost}/ws`;
        } else {
            // Production: Use relative path based on the current page's location
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.host;
            wsUrl = `${wsProtocol}//${wsHost}/ws`;
        }
        console.log(`Connecting WebSocket to: ${wsUrl}`);
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log('WebSocket connected');
            setIsWsConnected(true);
        }

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

        // Handle incoming messages from the WebSocket
        ws.current.onmessage = async (evt) => {
            const msg: ServerMsg = JSON.parse(await blobToText(evt.data));
            console.log('Received Websocket message:', msg);

            switch (msg.type) {
                /* full workbook ---------------------------------------------- */
                case 'workbook_update':
                    dispatch({type: 'REPLACE_WORKBOOK', wb: msg.payload});
                    break;

                /* incremental ops -------------------------------------------- */
                case 'apply_direct_updates':
                    sheetRef.current?.applyOperations(msg.payload.operations);
                    break;

                /* ask user to accept/reject ---------------------------------- */
                case 'propose_updates':
                    dispatch({type: 'QUEUE_OPS', ops: msg.payload.operations});
                    break;

                /* misc ------------------------------------------------------- */
                case 'session_created':
                    setSessionId(msg.payload.session_id);
                    Cookies.set('session_id', msg.payload.session_id, {expires: 1});
                    break;

                case 'chat_message':
                    setMessages((p) => [...p, msg.payload]);
                    break;

                default:
                    console.warn('Unknown WS message', msg);
            }
        };

        return () => {
            jsonWorker.current?.terminate();
            ws.current?.close();
        };
    }, [dispatch]);

    // --- File Upload Handler ---
    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!sessionId) {
            alert("Session not established. Please wait a moment or refresh the page.");
            return;
        }

        setMessages(prev => [...prev, {
            role: 'user',
            content: `Uploading file: ${file.name}`,
            timestamp: new Date().toISOString(),
        }]);

        const formData = new FormData();
        formData.append('file', file);

        const res = await axios.post('/upload', formData);
        dispatch({ type: 'REPLACE_WORKBOOK', wb: res.data });
    };

    const handleProcessBpss = useCallback(async (formData: FormData) => {
        if (!sessionId) {
            alert("Session not established. Please wait a moment or refresh the page.");
            return;
        }

        setIsBpssProcessing(true);
        setMessages(prev => [...prev, {
            role: 'user',
            content: 'Lancement du traitement BPSS...',
            timestamp: new Date().toISOString(),
        }]);

        try {
            const response = await axios.post<IWorkbookData>('/bpss/process', formData);
            dispatch({ type: 'REPLACE_WORKBOOK', wb: response.data });
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
    }, [dispatch, sessionId]);

    // --- Chat Message Sender ---
    const handleSendMessage = useCallback((messageText: string) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            // Add user's message to the chat UI immediately
            const userMessage: ChatMessage = {
                role: 'user',
                content: messageText,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, userMessage]);

            // Send the message to the backend
            const wsMessage = {
                type: 'user_message',
                payload: {content: messageText}
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

    const makeSmallUpdate = useCallback(async () => {
        if (!sessionId) {
            alert("Session not established. Please wait a moment or refresh the page.");
            return;
        }

        setMessages(prev => [...prev, {
            role: 'user',
            content: 'Performing a small update [debug]',
            timestamp: new Date().toISOString(),
        }]);

        try {
            await axios.post<IWorkbookData>('/perform_small_update');
        } catch (error: any) {
            console.error('Error processing performing small update:', error);
            const errorMessage = error.response?.data?.detail || 'An unknown error occurred.';
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `❌ Erreur lors de l'update : ${errorMessage}`,
                timestamp: new Date().toISOString(),
                error: true,
            }]);
        }
    }, [sessionId]);

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>BudgiBot UI</h1>
                <p>Session ID: {sessionId || 'Connecting...'}</p>
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
                        {state.workbook ? (
                            <UniverSheet
                                ref={sheetRef}
                                onCellChange={handleCellChange}
                                height={700}
                            />
                        ) : (
                            <div className="placeholder">
                                <p>Upload an Excel file to see it here.</p>
                                {!isWsConnected && <p style={{color: 'red'}}>Connecting to server...</p>}
                            </div>
                        )}
                        <button
                            onClick={makeSmallUpdate}
                            className="small-update-button"
                            disabled={!isWsConnected || !sessionId}>
                            Make Small Update [Debug]
                        </button>
                    </div>
                </div>
            </main>
            <UpdatesModal ws={ws.current}/>
        </div>
    );
}

export default App;