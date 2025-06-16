// frontend/src/services/chatApiServices.ts - Version complète

import type { ChatMessage } from '../types/contract';
import axios from 'axios';

export interface ChatUploadResponse {
    status: string;
    message: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const getBaseURL = () => {
    if (API_BASE_URL) {
        return API_BASE_URL;
    }
    // Make sure the path ends with a slash so relative paths are resolved correctly
    const path = window.location.pathname.endsWith('/')
        ? window.location.pathname
        : window.location.pathname + '/';
    return `${window.location.protocol}//${window.location.host}${path}`;
};

const apiClient = axios.create({
    baseURL: getBaseURL(),
    withCredentials: true,
});

export const uploadFileAndChat = async (
    file: File, 
    message: string = "", 
    chatHistory: ChatMessage[] = []
): Promise<ChatUploadResponse> => {
    console.log('🔍 Debug - uploadFileAndChat appelé avec:', {
        fileName: file.name,
        fileSize: file.size,
        message: message,
        historyLength: chatHistory.length,
        baseURL: getBaseURL()
    });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', message);
    formData.append('history', JSON.stringify(chatHistory));
    
    try {
        const response = await apiClient.post<ChatUploadResponse>('chat/upload_and_message', formData);
        console.log('🔍 Debug - Réponse réussie:', response.data);
        return response.data;
    } catch (error) {
        console.error('🔍 Debug - Erreur upload:', error);
        if (axios.isAxiosError(error)) {
            console.error('🔍 Debug - Détails erreur Axios:', {
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                url: error.config?.url
            });
            throw new Error(error.response?.data?.detail || `Erreur serveur (${error.response?.status})`);
        }
        throw error;
    }
};