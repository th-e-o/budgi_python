import axios from 'axios';
import type { IWorkbookData } from '@univerjs/core';
import type { ChatMessage } from '../types/contract';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
console.log(`Configuring API calls to: '${API_BASE_URL}'`);

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

export const uploadFile = async (file: File): Promise<IWorkbookData> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<IWorkbookData>('upload', formData);
  return response.data;
};

export const processBpss = async (formData: FormData): Promise<void> => {
  await apiClient.post('bpss/process', formData);
};

export const performSmallUpdate = async (): Promise<void> => {
  await apiClient.post('perform_small_update');
};

export interface ChatUploadResponse {
    status: string;
    message: string;
}

export const uploadFileAndChat = async (
    file: File, 
    message: string = "", 
    chatHistory: ChatMessage[] = []
): Promise<ChatUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', message);
    formData.append('history', JSON.stringify(chatHistory));
    
    const response = await fetch('/chat/upload_and_message', {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'upload du fichier');
    }
    
    return response.json();
};