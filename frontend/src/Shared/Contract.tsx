import type { IWorkbookData } from "@univerjs/presets";

// Shared type definitions for the application

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  error?: boolean;
}

export interface Operation {
  id: string;
  type: 'UPDATE_CELL' | 'CREATE_SHEET' | 'DELETE_SHEET' | 'REPLACE_SHEET';
  payload: any;
  description?: string;
}

export interface ServerMsg {
  type: string;
  payload: any;
}

// Specific message types from server
export interface WorkbookUpdateMsg extends ServerMsg {
  type: 'workbook_update';
  payload: IWorkbookData; // IWorkbookData
}

export interface ApplyDirectUpdatesMsg extends ServerMsg {
  type: 'apply_direct_updates';
  payload: {
    operations: Operation[];
  };
}

export interface ProposeUpdatesMsg extends ServerMsg {
  type: 'propose_updates';
  payload: {
    operations: Operation[];
  };
}

export interface SessionCreatedMsg extends ServerMsg {
  type: 'session_created';
  payload: {
    session_id: string;
  };
}

export interface ChatMessageMsg extends ServerMsg {
  type: 'chat_message';
  payload: ChatMessage;
}