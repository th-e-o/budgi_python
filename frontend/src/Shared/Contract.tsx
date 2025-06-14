import type { IWorkbookData } from "@univerjs/presets";

export interface Operation {
  id: string;
  type: 'CREATE_SHEET' | 'DELETE_SHEET' | 'UPDATE_CELL' | 'REPLACE_SHEET';
  description: string;
  // Everything Univer needs to replay the change:
  payload: Record<string, unknown>;
}

export type ServerMsg =
  | { type: 'session_created'; payload: { session_id: string } }
  | { type: 'chat_message'; payload: ChatMessage }
  | { type: 'workbook_update'; payload: IWorkbookData }
  | { type: 'apply_direct_updates'; payload: { operations: Operation[] } }
  | { type: 'propose_updates'; payload: { operations: Operation[] } };

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    error?: boolean;
}