import React, {useState, useRef, useEffect} from 'react';
import './ChatPanel.css';
import ReactMarkdown from 'react-markdown';
import BpssToolPanel from "./BpssToolPanel.tsx"; // For rendering markdown from bot

export interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    error?: boolean;
}

interface ChatPanelProps {
    messages: Message[];
    onSendMessage: (message: string) => void;
    onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
    onProcessBpss: (formData: FormData) => void;
    isBpssProcessing: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
                                                 messages,
                                                 onSendMessage,
                                                 onFileUpload,
                                                 onProcessBpss,
                                                 isBpssProcessing
                                             }) => {
    const [input, setInput] = useState('');
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

    const handleUploadButtonClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="chat-panel-container">
            <h2 className="chat-panel-header">Controls & Chat</h2>

            {/* This is the main file upload button for the whole app */}
            <div className="chat-controls">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={onFileUpload}
                    accept=".xlsx"
                    style={{display: 'none'}}
                />
                <button onClick={handleUploadButtonClick} className="upload-button">
                    📂 Upload Excel File
                </button>
            </div>

            <div className="messages-area">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-bubble ${msg.role} ${msg.error ? 'error' : ''}`}>
                        <div className="message-content">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef}/>
            </div>

            <form className="chat-input-form" onSubmit={handleSend}>
                <input
                    type="text"
                    className="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                />
                <button type="submit" className="send-button">Send</button>
            </form>

            <BpssToolPanel
                onProcess={onProcessBpss}
                isProcessing={isBpssProcessing}
            />
        </div>
    );
};

export default ChatPanel;