import React, {useState, useRef, useEffect} from 'react';
import ReactMarkdown from 'react-markdown';
import FileUploadArea from './FileUploadArea';
import './ChatPanel.css';
import BpssToolPanel from "./BpssToolPanel.tsx";
import type {ChatMessage} from "../types/contract.tsx"; // For rendering markdown from bot

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage: (message: string) => void;
    onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
    onProcessBpss: (formData: FormData) => void;
    isBpssProcessing: boolean;
    isConnected: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
                                                 messages,
                                                 onSendMessage,
                                                 onFileUpload,
                                                 onProcessBpss,
                                                 isBpssProcessing, 
                                                 isConnected
                                             }) => {
    const [input, setInput] = useState('');
    const [isFileProcessing, setIsFileProcessing] = useState(false);
    const [showFileUpload, setShowFileUpload] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim()) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleUploadStart = () => {
        setIsFileProcessing(true);
    };

    const handleUploadComplete = () => {
        setIsFileProcessing(false);
    };

    const handleExcelUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileError = (error: string) => {
        console.error('File upload error:', error);
        // Optionnellement ajouter un message d'erreur à l'interface
    };

    return (
        <div className="chat-panel-container">
            <h2 className="chat-panel-header">Controls & Chat</h2>

            {/* Upload Excel file - kept separate */}
            <div className="chat-controls">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={onFileUpload}
                    accept=".xlsx"
                    style={{ display: 'none' }}
                />
                <button onClick={handleExcelUploadClick} className="upload-button">
                    📊 Upload Excel File
                </button>
            </div>

            {/* File upload for chat */}
            <div className="chat-controls">
                <button 
                    onClick={() => setShowFileUpload(!showFileUpload)} 
                    className="upload-button secondary"
                    disabled={!isConnected}
                >
                    📄 {showFileUpload ? 'Masquer' : 'Ajouter un fichier au chat'}
                </button>
            </div>

            {showFileUpload && (
                <FileUploadArea
                    messages={messages}
                    onUploadStart={handleUploadStart}
                    onUploadComplete={handleUploadComplete}
                    onError={handleFileError}
                />
            )}

            <div className="messages-area">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-bubble ${msg.role} ${msg.error ? 'error' : ''}`}>
                        <div className="message-content">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                        <div className="message-timestamp">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                ))}
                
                {(isFileProcessing || isBpssProcessing) && (
                    <div className="message-bubble assistant">
                        <div className="message-content">
                            <span className="loading-indicator">⏳</span> 
                            {isFileProcessing ? 'Traitement du fichier...' : 'Traitement en cours...'}
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="chat-input-form">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isConnected ? "Tapez votre message..." : "Connexion en cours..."}
                    className="chat-input"
                    disabled={!isConnected || isFileProcessing}
                />
                <button 
                    type="submit" 
                    className="send-button"
                    disabled={!input.trim() || !isConnected || isFileProcessing}
                >
                    Envoyer
                </button>
            </form>

            {/* BPSS Tool Panel */}
            <BpssToolPanel
                onProcessBpss={onProcessBpss}
                isProcessing={isBpssProcessing}
                disabled={!isConnected}
            />
        </div>
    );
};

export default ChatPanel;