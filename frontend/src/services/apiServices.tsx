import axios from 'axios';
import type { IWorkbookData } from '@univerjs/core';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
console.log(`Configuring API calls to: '${API_BASE_URL}'`);

const apiClient = axios.create({
  baseURL: API_BASE_URL || `${window.location.protocol}//${window.location.host}`,
  withCredentials: true,
});

export const uploadFile = async (file: File): Promise<IWorkbookData> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<IWorkbookData>('/upload', formData);
  return response.data;
};

export const processBpss = async (formData: FormData): Promise<void> => {
  await apiClient.post('/bpss/process', formData);
};

export const performSmallUpdate = async (): Promise<void> => {
  await apiClient.post('/perform_small_update');
};