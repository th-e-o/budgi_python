import {type IWorksheetData} from '@univerjs/core';
import type {Operation} from '../Shared/Contract';
import {getUniverAPI} from '../ExcelViewer/UniverInstance';

/**
 * Applies backend-style operations to the **already loaded** workbook
 * without recreating the workbook from scratch.
 *
 * At this stage we only cover the four operation kinds
 * coming from UpdatedExcelHandler.
 */
export function applyOpsToUniver(
    ops: Operation[],
): void {
    console.log(`[applyOpsToUniver] Applying ${ops.length} operations to Univer workbook`);
    const univer = getUniverAPI();
    if (!univer) return;

    const wb = univer.getActiveWorkbook();
    if (!wb) return;

    console.log(`[applyOpsToUniver] Active workbook: ${wb.getName()}`);

    ops.forEach((op) => {
        console.log(`[applyOpsToUniver] Applying op ${op.id} of type ${op.type}`, op);
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
                    wb.getSheetByName(sheet)?.getRange(row, col).setValue(value.v);
                    break;
                }

                case 'REPLACE_SHEET': {
                    const worksheetData = op.payload as unknown as IWorksheetData
                    const existingSheet = wb.getSheetByName(worksheetData.name);
                    if (existingSheet) {
                        // If the sheet already exists, we delete it
                        wb.deleteSheet(existingSheet);
                    }
                    // Create a new sheet with the provided data
                    wb.create(
                        worksheetData.name,
                        worksheetData.rowCount,
                        worksheetData.columnCount,
                        {
                            index: wb.getNumSheets(),
                            sheet: worksheetData
                        });
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
