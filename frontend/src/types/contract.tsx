import type {ICellData, IWorkbookData, IWorksheetData } from "@univerjs/core";

// =================================================================
// Domain-Specific Types
// =================================================================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  error?: boolean;
}

// --- Operations ---
// By using a discriminated union for operations, we get type safety on the payload.

interface UpdateCellPayload {
  sheet: string;
  row: number;
  col: number;
  value: ICellData | null;
}

interface CreateSheetPayload {
  sheet_name: string;
}

interface DeleteSheetPayload {
  sheet_name: string;
}

type ReplaceSheetPayload = IWorksheetData;

export type Operation = { id: string; description?: string } & (
  | { type: 'UPDATE_CELL'; payload: UpdateCellPayload }
  | { type: 'CREATE_SHEET'; payload: CreateSheetPayload }
  | { type: 'DELETE_SHEET'; payload: DeleteSheetPayload }
  | { type: 'REPLACE_SHEET'; payload: ReplaceSheetPayload }
);


// =================================================================
// WebSocket Message Contracts
// =================================================================

// --- Server -> Client Messages ---

export type ServerMessage =
  | { type: 'session_created'; payload: { session_id: string } }
  | { type: 'workbook_update'; payload: IWorkbookData }
  | { type: 'apply_direct_updates'; payload: { operations: Operation[] } }
  | { type: 'propose_updates'; payload: { operations: Operation[] } }
  | { type: 'chat_message'; payload: ChatMessage };


// --- Client -> Server Messages ---

export type ClientMessage =
  | { type: 'user_message'; payload: { content: string } }
  | { type: 'cell_update'; payload: any } // Keeping 'any' for now as the Univer change format is complex
  | { type: 'validate_changes'; payload: { accepted: string[]; refused: string[] } };