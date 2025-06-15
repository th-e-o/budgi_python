import {type IWorksheetData} from '@univerjs/core';
import {getUniverAPI} from '../ExcelViewer/UniverInstance';
import type {Operation} from "../types/contract.tsx";
import type {FWorkbook} from '@univerjs/presets/lib/types/preset-sheets-core/index.js';

// =================================================================
// Types for Capturing Pre-Operation State
// =================================================================

type UpdateCellHistory = {
    type: 'UPDATE_CELL';
    sheetName: string;
    row: number;
    col: number;
    originalValue: any;
    originalFormula: string | null;
};

type CreateSheetHistory = {
    type: 'CREATE_SHEET';
    sheetName: string;
};

type SheetDataHistory = {
    type: 'DELETE_SHEET' | 'REPLACE_SHEET';
    sheetName: string;
    originalSheetSnapshot: IWorksheetData;
    originalIndex: number;
};

type OperationHistoryState = UpdateCellHistory | CreateSheetHistory | SheetDataHistory;

// =================================================================
// Module State
// =================================================================

/**
 * Stores the state of the workbook *before* an operation was applied.
 * This is essential for the rollback and re-apply (toggle) functionality.
 * This map is only cleared via `clearOperationHistory` after the user
 * has confirmed their validation choices.
 */
const operationHistory = new Map<string, OperationHistoryState>();

let isProgrammaticChangeInProgress = false;
export const isApplyingProgrammaticChange = () => isProgrammaticChangeInProgress;

// =================================================================
// Private Helper Functions
// =================================================================

/**
 * Captures the current state of the workbook related to a specific operation
 * before it is applied. This captured state is used for potential rollbacks.
 * @returns The state object to be stored, or null if capture fails.
 */
function captureStateBeforeOperation(op: Operation, wb: FWorkbook): OperationHistoryState | null {
    switch (op.type) {
        case 'UPDATE_CELL': {
            const {sheet: sheetName, row, col} = op.payload;
            const targetSheet = wb.getSheetByName(sheetName);
            if (!targetSheet) return null;

            const cell = targetSheet.getRange(row, col);
            return {
                type: 'UPDATE_CELL',
                sheetName,
                row,
                col,
                originalValue: cell.getValue(),
                originalFormula: cell.getFormula(),
            };
        }

        case 'CREATE_SHEET': {
            return {
                type: 'CREATE_SHEET',
                sheetName: op.payload.sheet_name,
            };
        }

        case 'DELETE_SHEET': {
            const {sheet_name} = op.payload;
            const sheet = wb.getSheetByName(sheet_name);
            if (!sheet) return null;

            return {
                type: 'DELETE_SHEET',
                sheetName: sheet_name,
                originalSheetSnapshot: wb.getSnapshot().sheets[sheet.getSheetId()] as IWorksheetData,
                originalIndex: sheet.getIndex(),
            };
        }

        case 'REPLACE_SHEET': {
            const sheetName = op.payload.name;
            const sheet = wb.getSheetByName(sheetName);
            if (!sheet) return null; // Can't replace a sheet that doesn't exist

            return {
                type: 'REPLACE_SHEET',
                sheetName,
                originalSheetSnapshot: wb.getSnapshot().sheets[sheet.getSheetId()] as IWorksheetData,
                originalIndex: sheet.getIndex(),
            };
        }

        default:
            // This case should not be reachable with a well-typed `Operation` union
            return null;
    }
}

// =================================================================
// Public API
// =================================================================

/**
 * Applies a list of operations to the active Univer workbook.
 * This modifies the workbook in-place for performance.
 *
 * @param ops - An array of operations to apply.
 * @param captureHistory - If true, captures the pre-operation state for rollback.
 */
export function applyOpsToUniver(
    ops: Operation[],
    captureHistory: boolean = true
): void {
    const univer = getUniverAPI();
    if (!univer) {
        console.error('[applyOpsToUniver] Univer API not available.');
        return;
    }

    const wb = univer.getActiveWorkbook();
    if (!wb) {
        console.error('[applyOpsToUniver] No active workbook.');
        return;
    }

    isProgrammaticChangeInProgress = true;

    try {
        ops.forEach((op) => {
            if (captureHistory && !operationHistory.has(op.id)) {
                const originalState = captureStateBeforeOperation(op, wb);
                if (originalState) {
                    console.log(`[applyOpsToUniver] Capturing initial state for op ${op.id}`, originalState);
                    operationHistory.set(op.id, originalState);
                } else {
                    console.warn(`[applyOpsToUniver] Could not capture state for op ${op.id}`);
                }
            }

            try {
                switch (op.type) {
                    case 'CREATE_SHEET': {
                        wb.create(op.payload.sheet_name, 300, 52); // Using default dimensions
                        break;
                    }

                    case 'DELETE_SHEET': {
                        const sheet = wb.getSheetByName(op.payload.sheet_name);
                        if (sheet) {
                            wb.deleteSheet(sheet);
                        } else {
                            console.warn(`[applyOpsToUniver] Sheet "${op.payload.sheet_name}" not found for deletion.`);
                        }
                        break;
                    }

                    case 'UPDATE_CELL': {
                        const {sheet: sheetName, row, col, value} = op.payload;
                        const targetSheet = wb.getSheetByName(sheetName);
                        if (!targetSheet) {
                            console.warn(`[applyOpsToUniver] Sheet "${sheetName}" not found for cell update.`);
                            break;
                        }
                        const range = targetSheet.getRange(row, col);
                        const cellValue = value?.v !== undefined ? value.v : value;
                        if (cellValue === null || cellValue === undefined) range.clearContent()
                        else range.setValue(cellValue);
                        break;
                    }

                    case 'REPLACE_SHEET': {
                        const newSheetData = op.payload;
                        const oldSheet = wb.getSheetByName(newSheetData.name);

                        if (oldSheet) {
                            const index = oldSheet.getIndex();
                            wb.deleteSheet(oldSheet);
                            // Create a new sheet with the new data at the old index to preserve order
                            wb.create(newSheetData.name, newSheetData.rowCount, newSheetData.columnCount, {
                                index,
                                sheet: newSheetData,
                            });
                        } else {
                            // If it doesn't exist, just create it at the end
                            wb.create(newSheetData.name, newSheetData.rowCount, newSheetData.columnCount, {
                                sheet: newSheetData,
                            });
                        }
                        break;
                    }
                }
            } catch (err) {
                console.error(`[applyOpsToUniver] Failed to apply op ${op.id}:`, err);
            }
        });
    } finally {
        isProgrammaticChangeInProgress = false;
    }
}

/**
 * Reverts a single operation using its stored history.
 *
 * @param op - The operation to roll back.
 * @returns True if the rollback was successful, false otherwise.
 */
export function rollbackOperation(op: Operation): boolean {
    const univer = getUniverAPI();
    if (!univer) return false;
    const wb = univer.getActiveWorkbook();
    if (!wb) return false;

    const originalState = operationHistory.get(op.id);
    if (!originalState) {
        console.warn(`[rollbackOperation] No history found for operation ${op.id}. Cannot roll back.`);
        return false;
    }

    console.log(`[rollbackOperation] Rolling back op ${op.id} of type ${originalState.type}`);
    isProgrammaticChangeInProgress = true;
    try {
        switch (originalState.type) {
            case 'UPDATE_CELL': {
                const {sheetName, row, col, originalValue, originalFormula} = originalState;
                const targetSheet = wb.getSheetByName(sheetName);
                if (!targetSheet) return false;

                const cell = targetSheet.getRange(row, col);
                // Prioritize restoring the formula if it existed, otherwise restore the value.
                if (originalFormula) {
                    cell.setFormula(originalFormula);
                } else {
                    if (originalValue === null || originalValue === undefined) cell.clearContent()
                    else cell.setValue(originalValue);
                }
                break;
            }

            case 'CREATE_SHEET': {
                const sheet = wb.getSheetByName(originalState.sheetName);
                if (sheet) {
                    wb.deleteSheet(sheet);
                }
                break;
            }

            case 'DELETE_SHEET':
            case 'REPLACE_SHEET': {
                // To roll back a delete or replace, we restore the original sheet snapshot.
                const {originalSheetSnapshot, originalIndex} = originalState;
                const existingSheet = wb.getSheetByName(originalSheetSnapshot.name);
                // If a sheet with the same name was created by the rollback, delete it first.
                if (existingSheet) {
                    wb.deleteSheet(existingSheet);
                }
                wb.create(
                    originalSheetSnapshot.name,
                    originalSheetSnapshot.rowCount,
                    originalSheetSnapshot.columnCount,
                    {index: originalIndex, sheet: originalSheetSnapshot}
                );
                break;
            }
        }
        return true;
    } catch (err) {
        console.error(`[rollbackOperation] Failed to roll back operation ${op.id}`, err);
        return false;
    } finally {
        isProgrammaticChangeInProgress = false;
    }
}

/**
 * Clears the stored history for specific operation IDs.
 * This should be called after the user confirms their validation choices.
 */
export function clearOperationHistory(operationIds: string[]): void {
    console.log(`[clearOperationHistory] Clearing history for ${operationIds.length} operations.`);
    operationIds.forEach(id => operationHistory.delete(id));
}