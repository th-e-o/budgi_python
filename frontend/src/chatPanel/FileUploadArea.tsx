import React, { useRef, useState } from 'react';
import { uploadFileAndChat } from '../services/chatApiServices';
import type { ChatMessage } from '../types/contract';

interface FileUploadAreaProps {
    messages: ChatMessage[];  // Historique actuel
    onUploadStart: () => void;
    onUploadComplete: () => void;
    onError: (error: string) => void;
}

const FileUploadArea: React.FC<FileUploadAreaProps> = ({ 
    messages,
    onUploadStart, 
    onUploadComplete, 
    onError 
}) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploadMessage, setUploadMessage] = useState('');

    const handleFileSelect = async (file: File, message: string = '') => {
        const validTypes = ['.pdf', '.docx', '.txt', '.msg'];
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
        
        if (!validTypes.includes(fileExt)) {
            onError(`Type de fichier non supporté: ${fileExt}. Types acceptés: PDF, Word, TXT, MSG`);
            return;
        }

        try {
            onUploadStart();
            
            // Upload le fichier avec l'historique - le serveur gère tout le reste
            await uploadFileAndChat(file, message, messages);
            
            // Pas besoin de gérer la réponse - elle arrive via WebSocket
            setUploadMessage('');
            onUploadComplete();
            
        } catch (error) {
            onError(`Erreur lors de l'upload: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
            onUploadComplete();
        }
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            handleFileSelect(file, uploadMessage);
        }
        // Reset input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileSelect(file, uploadMessage);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
    };

    return (
        <div className="file-upload-area">
            <div
                className={`drop-zone ${dragActive ? 'active' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,.msg"
                    onChange={handleFileInputChange}
                    style={{ display: 'none' }}
                />
                <div className="drop-zone-content">
                    <span className="upload-icon">📄</span>
                    <p>Glissez un fichier ici ou cliquez pour sélectionner</p>
                    <small>Formats supportés: PDF, Word, TXT, MSG</small>
                </div>
            </div>
            
            <div className="upload-message-input">
                <input
                    type="text"
                    placeholder="Message optionnel à envoyer avec le fichier..."
                    value={uploadMessage}
                    onChange={(e) => setUploadMessage(e.target.value)}
                    className="message-input"
                />
            </div>
        </div>
    );
};

export default FileUploadArea;
