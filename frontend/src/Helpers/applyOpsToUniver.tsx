import {type IWorksheetData} from '@univerjs/core';
import type {Operation} from '../Shared/Contract';
import {getUniverAPI} from '../ExcelViewer/UniverInstance';

// Store for original states to enable rollback
const operationHistory = new Map<string, any>();

/**
 * Captures the current state before applying an operation
 */
function captureStateBeforeOperation(op: Operation): any {
    const univer = getUniverAPI();
    if (!univer) return null;

    const wb = univer.getActiveWorkbook();
    if (!wb) return null;

    switch (op.type) {
        case 'UPDATE_CELL': {
            const {sheet, row, col} = op.payload as any;
            const targetSheet = wb.getSheetByName(sheet);
            if (!targetSheet) return null;

            const cell = targetSheet.getRange(row, col);
            const originalValue = cell.getValue();
            const originalFormula = cell.getFormula();

            return {
                type: 'UPDATE_CELL',
                sheet,
                row,
                col,
                originalValue: originalValue,
                originalFormula: originalFormula,
                hadValue: originalValue !== null && originalValue !== undefined && originalValue !== ''
            };
        }

        case 'CREATE_SHEET': {
            // For create, we just need to remember it was created
            return {
                type: 'CREATE_SHEET',
                sheet_name: (op.payload as any).sheet_name
            };
        }

        case 'DELETE_SHEET': {
            const {sheet_name} = op.payload as any;
            const sheet = wb.getSheetByName(sheet_name);
            if (!sheet) return null;

            // Capture sheet data before deletion
            const rowCount = sheet.getMaxRows();
            const colCount = sheet.getMaxColumns();
            const cellData: any = {};

            // Capture all cell data
            for (let r = 0; r < rowCount; r++) {
                for (let c = 0; c < colCount; c++) {
                    const cell = sheet.getRange(r, c);
                    const value = cell.getValue();
                    const formula = cell.getFormula();
                    if (value !== null || formula) {
                        if (!cellData[r]) cellData[r] = {};
                        cellData[r][c] = {
                            v: value,
                            f: formula
                        };
                    }
                }
            }

            return {
                type: 'DELETE_SHEET',
                sheet_name,
                sheetData: {
                    name: sheet_name,
                    rowCount,
                    columnCount: colCount,
                    cellData
                }
            };
        }

        case 'REPLACE_SHEET': {
            const worksheetData = op.payload as unknown as IWorksheetData;
            const existingSheet = wb.getSheetByName(worksheetData.name);

            if (existingSheet) {
                // Capture current sheet state
                const rowCount = existingSheet.getMaxRows();
                const colCount = existingSheet.getMaxColumns();
                const cellData: any = {};

                for (let r = 0; r < rowCount; r++) {
                    for (let c = 0; c < colCount; c++) {
                        const cell = existingSheet.getRange(r, c);
                        const value = cell.getValue();
                        const formula = cell.getFormula();
                        if (value !== null || formula) {
                            if (!cellData[r]) cellData[r] = {};
                            cellData[r][c] = {
                                v: value,
                                f: formula
                            };
                        }
                    }
                }

                return {
                    type: 'REPLACE_SHEET',
                    sheetData: {
                        name: worksheetData.name,
                        rowCount,
                        columnCount: colCount,
                        cellData
                    }
                };
            }

            return null;
        }

        default:
            return null;
    }
}

/**
 * Applies backend-style operations to the **already loaded** workbook
 * without recreating the workbook from scratch.
 * Now with rollback support.
 */
export function applyOpsToUniver(
    ops: Operation[],
    captureHistory: boolean = true
): void {
    console.log(`[applyOpsToUniver] Applying ${ops.length} operations to Univer workbook`);
    const univer = getUniverAPI();
    if (!univer) return;

    const wb = univer.getActiveWorkbook();
    if (!wb) return;

    console.log(`[applyOpsToUniver] Active workbook: ${wb.getName()}`);

    ops.forEach((op) => {
        console.log(`[applyOpsToUniver] Applying op ${op.id} of type ${op.type}`, op);

        // Capture state before operation for rollback
        if (captureHistory) {
            const originalState = captureStateBeforeOperation(op);
            if (originalState) {
                operationHistory.set(op.id, originalState);
            }
        }

        try {
            switch (op.type) {
                case 'CREATE_SHEET': {
                    // Payload: { sheet_name: string }
                    const {sheet_name} = op.payload as any;
                    wb.create(sheet_name, 300, 52); // basic API
                    break;
                }

                case 'DELETE_SHEET': {
                    const {sheet_name} = op.payload as any;
                    const sheet = wb.getSheetByName(sheet_name);
                    if (!sheet) {
                        console.warn(`[applyOpsToUniver] Sheet ${sheet_name} not found`);
                        return;
                    }
                    const deleted = wb.deleteSheet(sheet)
                    if (!deleted) {
                        console.warn(`[applyOpsToUniver] Failed to delete sheet ${sheet_name}`);
                    } else {
                        console.log(`[applyOpsToUniver] Deleted sheet ${sheet_name}`);
                    }
                    break;
                }

                case 'UPDATE_CELL': {
                    const {sheet, row, col, value} = op.payload as any;
                    const targetSheet = wb.getSheetByName(sheet);
                    if (!targetSheet) {
                        console.warn(`[applyOpsToUniver] Sheet ${sheet} not found`);
                        break;
                    }
                    const range = targetSheet.getRange(row, col);
                    if (!range) {
                        console.warn(`[applyOpsToUniver] Range [${row},${col}] not found in sheet ${sheet}`);
                        break;
                    }
                    // Handle different value types
                    const cellValue = value?.v !== undefined ? value.v : value;
                    range.setValue(cellValue);
                    break;
                }

                case 'REPLACE_SHEET': {
                    const worksheetData = op.payload as unknown as IWorksheetData
                    const existingSheet = wb.getSheetByName(worksheetData.name);

                    const maxRow = worksheetData.rowCount
                    const maxCol = worksheetData.columnCount

                    if (existingSheet) {
                        existingSheet.setRowCount(maxRow)
                        existingSheet.setColumnCount(maxCol)
                        const range = existingSheet.getRange(0, 0, maxRow, maxCol)
                        range.setValues(worksheetData.cellData)
                    } else {
                        wb.create(worksheetData.name, maxRow, maxCol, {
                            index: wb.getSheets().length,
                            sheet: worksheetData
                        })
                    }

                    break;
                }

                default:
                    console.warn(`[applyOpsToUniver] Unknown op: ${op.type}`);
            }
        } catch (err) {
            console.error(`[applyOpsToUniver] Failed op ${op.id}`, err);
        }
    });
}

/**
 * Rollback a single operation using stored history
 */
export function rollbackOperation(op: Operation): boolean {
    const univer = getUniverAPI();
    if (!univer) return false;

    const wb = univer.getActiveWorkbook();
    if (!wb) return false;

    const originalState = operationHistory.get(op.id);
    if (!originalState) {
        console.warn(`[rollbackOperation] No history found for operation ${op.id}`);
        return false;
    }

    console.log(`[rollbackOperation] Rolling back operation ${op.id} of type ${originalState.type}`);

    try {
        switch (originalState.type) {
            case 'UPDATE_CELL': {
                const {sheet, row, col, originalValue, originalFormula, hadValue} = originalState;
                const targetSheet = wb.getSheetByName(sheet);
                if (!targetSheet) return false;

                const cell = targetSheet.getRange(row, col);
                if (originalFormula) {
                    cell.setValue(originalFormula);
                } else if (hadValue) {
                    cell.setValue(originalValue);
                } else {
                    // Clear the cell if it was originally empty
                    cell.setValue('');
                }
                break;
            }

            case 'CREATE_SHEET': {
                // To rollback a create, we delete the sheet
                const {sheet_name} = originalState;
                const sheet = wb.getSheetByName(sheet_name);
                if (sheet) {
                    wb.deleteSheet(sheet);
                }
                break;
            }

            case 'DELETE_SHEET': {
                // To rollback a delete, we recreate the sheet with its data
                const {sheetData} = originalState;
                wb.create(sheetData.name, sheetData.rowCount, sheetData.columnCount, {
                    index: wb.getSheets().length,
                    sheet: sheetData
                });
                break;
            }

            case 'REPLACE_SHEET': {
                // Restore the original sheet data
                const {sheetData} = originalState;
                const existingSheet = wb.getSheetByName(sheetData.name);

                if (existingSheet) {
                    existingSheet.setRowCount(sheetData.rowCount);
                    existingSheet.setColumnCount(sheetData.columnCount);
                    const range = existingSheet.getRange(0, 0, sheetData.rowCount, sheetData.columnCount);
                    range.setValues(sheetData.cellData);
                }
                break;
            }
        }

        // Remove from history after successful rollback
        operationHistory.delete(op.id);
        return true;
    } catch (err) {
        console.error(`[rollbackOperation] Failed to rollback operation ${op.id}`, err);
        return false;
    }
}

/**
 * Clear operation history for a set of operations
 */
export function clearOperationHistory(operationIds: string[]): void {
    operationIds.forEach(id => operationHistory.delete(id));
}

/**
 * Clear all operation history
 */
export function clearAllOperationHistory(): void {
    operationHistory.clear();
}