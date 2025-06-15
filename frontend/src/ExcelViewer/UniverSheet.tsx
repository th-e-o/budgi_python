import {
    createUniver,
    defaultTheme,
    FUniver,
    LocaleType,
    merge,
} from "@univerjs/presets";
import {CalculationMode, UniverSheetsCorePreset} from "@univerjs/presets/preset-sheets-core";
import UniverPresetSheetsCoreFrFR from "@univerjs/presets/preset-sheets-core/locales/fr-FR";
import {UniverSheetsDataValidationPreset} from "@univerjs/presets/preset-sheets-data-validation";
import UniverPresetSheetsDataValidationFrFR from "@univerjs/presets/preset-sheets-data-validation/locales/fr-FR";
import "@univerjs/presets/lib/styles/preset-sheets-core.css";
import "@univerjs/presets/lib/styles/preset-sheets-data-validation.css";

import {forwardRef, useEffect, useImperativeHandle, useRef} from "react";
// import {type IDisposable, type IWorkbookData} from "@univerjs/core";
import {type IDisposable, type IWorkbookData} from "@univerjs/core";
import type {Operation} from "../Shared/Contract.tsx";
import {applyOpsToUniver} from "../Helpers/applyOpsToUniver.tsx";
import {setUniverAPI} from "./UniverInstance.tsx";
import {useWorkbook} from "./WorkbookContext.tsx";

export interface UniverSheetHandle {
    applyOperations: (ops: Operation[]) => void;
    recalculateFormulas: () => void;
}

// Define the props our component will accept
interface Props {
    onCellChange: (changeData: any) => void;
    onCalculationEnd?: () => void;
    height?: number;
}

const UniverSheet = forwardRef<UniverSheetHandle, Props>(
    ({onCellChange, onCalculationEnd, height = 800}, ref) => {
        const {state} = useWorkbook();
        const containerRef = useRef<HTMLDivElement>(null);
        const univerApiRef = useRef<FUniver | null>(null);
        const loadedPointer = useRef<IWorkbookData | null>(null);

        useImperativeHandle(ref, () => ({
            applyOperations: (ops: Operation[]) => applyOpsToUniver(ops),
            recalculateFormulas: () => {
                const formula = univerApiRef.current?.getFormula();
                if (formula) {
                    console.log("Manual formula recalculation triggered.");
                    formula.executeCalculation();
                }
            }
        }));

        const isLoadingRef = useRef<boolean>(false);

        useEffect(() => {
            if (!containerRef.current || univerApiRef.current) return;

            const {univerAPI} = createUniver({
                locale: LocaleType.FR_FR,
                locales: {[LocaleType.FR_FR]: merge({}, UniverPresetSheetsCoreFrFR, UniverPresetSheetsDataValidationFrFR)},
                theme: defaultTheme,
                presets: [
                    UniverSheetsCorePreset({
                        container: containerRef.current,
                        ribbonType: 'simple',
                        header: true,
                        toolbar: true,
                        contextMenu: true,
                        statusBarStatistic: false,
                        formula: {
                            initialFormulaComputing: CalculationMode.NO_CALCULATION,
                        },
                    }),
                    UniverSheetsDataValidationPreset(),
                ],
            });

            univerApiRef.current = univerAPI;
            setUniverAPI(univerAPI);

            const disposables: IDisposable[] = [];
            const formula = univerAPI.getFormula();

            disposables.push(formula.calculationEnd(() => {
                onCalculationEnd?.();
            }));


            disposables.push(formula.calculationEnd(() => {
                onCalculationEnd?.();
            }));

            disposables.push(formula.calculationStart((forceCalculation) => {
                const currentFormula = univerApiRef.current?.getFormula();
                if (forceCalculation){
                    console.log("Manual calculation has started with force calculation.");
                } else {
                    console.log("Canceling automatic calculation as it was not forced.");
                    currentFormula?.stopCalculation();
                }
            }));

            /* --- Cell-change listener (unchanged) ------------------------ */
            disposables.push(univerAPI.addEvent(univerAPI.Event.SheetValueChanged, async (params: any) => {
                if (isLoadingRef.current) return;
                console.log("Started processing change message")
                const payload = params.payload;

                if (!payload || !payload.params || !payload.params.cellValue || payload.id !== "sheet.mutation.set-range-values") {
                    console.warn("Invalid payload, skipping debounced processing.");
                    return;
                }

                const worksheetId = payload.params.subUnitId;
                const workbook = univerApiRef.current?.getActiveWorkbook();
                if (!workbook) return;

                const modifiedSheet = workbook.getSheetBySheetId(worksheetId);

                if (!modifiedSheet) {
                    console.warn("Sheet not found in workbook. Skipping change.");
                    return;
                }

                const originalChange = payload.params.cellValue;
                const filteredChange: { [key: string]: { [key: string]: any } } = {};
                let hasValidChanges = false;

                // This entire block is now deferred and won't block the UI
                Object.entries(originalChange).forEach(([rowIndex, rowData]) => {
                    const rowChanges: { [key: string]: any } = {};
                    let rowHasValidChanges = false;
                    Object.entries(rowData as object).forEach(([colIndex, cellData]) => {
                        const cell = modifiedSheet.getRange(parseInt(rowIndex), parseInt(colIndex));
                        if (!cell?.getFormula()) {
                            rowChanges[colIndex] = cellData;
                            rowHasValidChanges = true;
                            hasValidChanges = true;
                        }
                    });
                    if (rowHasValidChanges) {
                        filteredChange[rowIndex] = rowChanges;
                    }
                });

                if (!hasValidChanges) {
                    console.log("Debounced processing found no non-formula changes. Skipping send.");
                    return;
                }

                const changeData = {
                    sheet: modifiedSheet.getSheetName() ?? "Unknown",
                    value: filteredChange,
                    timestamp: Date.now(),
                };

                onCellChange(changeData);
            }));
        }, [onCellChange, onCalculationEnd]);

        useEffect(() => {
            if (!univerApiRef.current || !state.workbook) return;
            if (loadedPointer.current === state.workbook) return; // already loaded
            isLoadingRef.current = true;

            console.log('[UniverSheet] Creating workbook from JSON');
            loadedPointer.current = state.workbook;

            // dispose old one
            univerApiRef.current.getActiveWorkbook()?.dispose();

            // create new
            console.log('[UniverSheet] Workbook data:', state.workbook);
            const wb = univerApiRef.current.createWorkbook(state.workbook);
            wb?.getSheets()?.[0]?.activate();

            isLoadingRef.current = false;
        }, [state.workbook]);

        return (
            <div
                ref={containerRef}
                className="univer-sheet-container"
                style={{
                    width: "100%",
                    height: `${height}px`,
                    border: "1px solid #e0e0e0",
                    borderRadius: "4px",
                    overflow: 'hidden',
                }}
            />
        );
    }
);

export default UniverSheet;