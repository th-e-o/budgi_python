import React, {useState, useEffect, useRef, useCallback} from 'react';
import Cookies from 'js-cookie';
import UniverSheet, {type UniverSheetHandle} from './ExcelViewer/UniverSheet';
import ChatPanel from './chatPanel/ChatPanel';
import ValidationToolbar from './Components/ValidationToolbar';
import {useWorkbook} from "./ExcelViewer/WorkbookContext";
import {useAppWebSocket} from './hooks/useAppWebSocket';
import * as api from './services/apiServices';
import type {ChatMessage} from './types/contract.tsx';
import './App.css';

function App() {
    const {state: workbookState, dispatch: workbookDispatch} = useWorkbook();
    const {connectionStatus, lastMessage, sendMessage} = useAppWebSocket();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [sessionId, setSessionId] = useState<string | null>(Cookies.get('session_id') || null);
    const [isBpssProcessing, setIsBpssProcessing] = useState(false);
    const [isCalculating, setIsCalculating] = useState(false);

    const sheetRef = useRef<UniverSheetHandle | null>(null);

    const isConnected = connectionStatus === 'connected';
    const hasValidations = workbookState.pendingOps.length > 0;

    // --- Message Handler: React to messages from the WebSocket hook ---
    useEffect(() => {
        if (!lastMessage) return;

        switch (lastMessage.type) {
            case 'session_created':
                setSessionId(lastMessage.payload.session_id);
                Cookies.set('session_id', lastMessage.payload.session_id, {expires: 1});
                break;
            case 'workbook_update':
                workbookDispatch({type: 'REPLACE_WORKBOOK', wb: lastMessage.payload});
                break;
            case 'apply_direct_updates':
                sheetRef.current?.applyOperations(lastMessage.payload.operations);
                break;
            case 'propose_updates':
                workbookDispatch({type: 'QUEUE_OPS', ops: lastMessage.payload.operations});
                break;
            case 'chat_message':
                setMessages((prev) => [...prev, lastMessage.payload]);
                break;
            default:
                console.warn('Unknown WS message type:', (lastMessage as any).type);
        }
    }, [lastMessage, workbookDispatch]);

    // Effect for handling disconnection
    useEffect(() => {
        if (connectionStatus === 'disconnected') {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'System: Connection to server lost. Please refresh the page.',
                timestamp: new Date().toISOString(),
                error: true,
            }]);
        }
    }, [connectionStatus])

    // --- UI Action Handlers ---

    const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !sessionId) return;

        setMessages(prev => [...prev, {
            role: 'user', content: `Uploading file: ${file.name}`, timestamp: new Date().toISOString(),
        }]);

        try {
            const workbookData = await api.uploadFile(file);
            workbookDispatch({type: 'REPLACE_WORKBOOK', wb: workbookData});
        } catch (error) {
            console.error("File upload failed:", error);
            // You can add an error message to the chat here
        }
    }, [sessionId, workbookDispatch]);

    const handleProcessBpss = useCallback(async (formData: FormData) => {
        if (!sessionId) return;
        setIsBpssProcessing(true);
        setMessages(prev => [...prev, {
            role: 'user', content: 'Lancement du traitement BPSS...', timestamp: new Date().toISOString(),
        }]);

        try {
            await api.processBpss(formData);
        } catch (error) {
            console.error("BPSS processing failed:", error);
        } finally {
            setIsBpssProcessing(false);
        }
    }, [sessionId]);

    const handleSendMessage = useCallback((messageText: string) => {
        if (!isConnected) {
            console.warn('WebSocket is not connected. Cannot send message.');
            return;
        }
        const userMessage: ChatMessage = {
            role: 'user', content: messageText, timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);
        sendMessage('user_message', {content: messageText});
    }, [isConnected, sendMessage]);

    const handleCellChange = useCallback((changeData: any) => {
        sendMessage('cell_update', changeData);
    }, [sendMessage]);

    const handleValidationConfirm = useCallback((acceptedIds: string[], refusedIds: string[]) => {
        sendMessage('validate_changes', {accepted: acceptedIds, refused: refusedIds});
        workbookDispatch({type: 'CLEAR_PENDING'});
    }, [sendMessage, workbookDispatch]);

    const handleRecalculate = useCallback(() => {
        setIsCalculating(true);
        sheetRef.current?.recalculateFormulas();
    }, []);

    const handleCalculationEnd = useCallback(() => setIsCalculating(false), []);

    const makeSmallUpdate = useCallback(async () => {
        if (!sessionId) return;
        setMessages(p => [...p, {
            role: 'user',
            content: 'Performing a small update [debug]',
            timestamp: new Date().toISOString()
        }]);
        try {
            await api.performSmallUpdate();
        } catch (error: any) {
            console.error('Error performing small update:', error);
            const errorMessage = error.response?.data?.detail || 'An unknown error occurred.';
            setMessages(p => [...p, {
                role: 'assistant',
                content: `❌ Error during update: ${errorMessage}`,
                timestamp: new Date().toISOString(),
                error: true
            }]);
        }
    }, [sessionId]);


    return (
        <div className={`app-container ${hasValidations ? 'has-validations' : ''}`}>
            <header className="app-header">
                <h1>BudgiBot UI</h1>
                <p>Session ID: {sessionId || 'Connecting...'} | Status: {connectionStatus}</p>
            </header>

            <main className="main-content">
                <div className="layout-grid">
                    <ChatPanel
                        messages={messages}
                        onSendMessage={handleSendMessage}
                        onFileUpload={handleFileUpload}
                        onProcessBpss={handleProcessBpss}
                        isBpssProcessing={isBpssProcessing}
                    />

                    <div className="panel excel-panel">
                        <h2>Excel Viewer</h2>
                        <UniverSheet
                            ref={sheetRef}
                            onCellChange={handleCellChange}
                            onCalculationEnd={handleCalculationEnd}
                            height={700}
                        />
                        <button onClick={handleRecalculate} disabled={!isConnected || !sessionId || isCalculating}>
                            {isCalculating ? 'Calculating...' : 'Recalculate Formulas'}
                        </button>
                        <button onClick={makeSmallUpdate} disabled={!isConnected || !sessionId}>
                            Make Small Update [Debug]
                        </button>
                    </div>
                </div>
            </main>

            {hasValidations && (
                <ValidationToolbar onConfirm={handleValidationConfirm}/>
            )}
        </div>
    );
}

export default App;