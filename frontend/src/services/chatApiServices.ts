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