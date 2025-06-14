import {
    createUniver,
    defaultTheme,
    FUniver,
    LocaleType,
    merge,
} from "@univerjs/presets";
import {UniverSheetsCorePreset} from "@univerjs/presets/preset-sheets-core";
import UniverPresetSheetsCoreFrFR from "@univerjs/presets/preset-sheets-core/locales/fr-FR";
import {UniverSheetsDataValidationPreset} from "@univerjs/presets/preset-sheets-data-validation";
import UniverPresetSheetsDataValidationFrFR from "@univerjs/presets/preset-sheets-data-validation/locales/fr-FR";
import "@univerjs/presets/lib/styles/preset-sheets-core.css";
import "@univerjs/presets/lib/styles/preset-sheets-data-validation.css";

import {forwardRef, useEffect, useImperativeHandle, useRef} from "react";
import {type IDisposable, type IWorkbookData} from "@univerjs/core";
import type {Operation} from "../Shared/Contract.tsx";
import {applyOpsToUniver} from "../Helpers/applyOpsToUniver.tsx";
import {setUniverAPI} from "./UniverInstance.tsx";
import {useWorkbook} from "./WorkbookContext.tsx";

export interface UniverSheetHandle {
    applyOperations: (ops: Operation[]) => void;
}

// Define the props our component will accept
interface Props {
    onCellChange: (changeData: any) => void;
    height?: number;
}

const UniverSheet = forwardRef<UniverSheetHandle, Props>(
    ({onCellChange, height = 800}, ref) => {
        const {state} = useWorkbook();
        const containerRef = useRef<HTMLDivElement>(null);
        const univerRef = useRef<FUniver | null>(null);
        const loadedPointer = useRef<IWorkbookData | null>(null);

        useImperativeHandle(ref, () => ({
            applyOperations: (ops: Operation[]) => applyOpsToUniver(ops)
        }));

        const isLoadingRef = useRef<boolean>(false);
        const calculationProcessingCallback = useRef<IDisposable | null>(null);

        useEffect(() => {
            if (!containerRef.current || univerRef.current) return;

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
                    }),
                    UniverSheetsDataValidationPreset(),
                ],
            });
            univerRef.current = univerAPI;
            setUniverAPI(univerAPI);

            /* --- Cell-change listener (unchanged) ------------------------ */
            univerAPI.addEvent(univerAPI.Event.SheetValueChanged, async (params: any) => {
                if (isLoadingRef.current) return;
                console.log("Started processing change message")
                const payload = params.payload;

                if (!payload || !payload.params || !payload.params.cellValue || payload.id !== "sheet.mutation.set-range-values") {
                    console.warn("Invalid payload, skipping debounced processing.");
                    return;
                }

                const worksheetId = payload.params.subUnitId;
                const workbook = univerRef.current?.getActiveWorkbook();
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
            });
        }, [onCellChange]);

        useEffect(() => {
            if (!univerRef.current || !state.workbook) return;
            if (loadedPointer.current === state.workbook) return; // already loaded
            isLoadingRef.current = true;

            console.log('[UniverSheet] Creating workbook from JSON');
            loadedPointer.current = state.workbook;

            // dispose old one
            univerRef.current.getActiveWorkbook()?.dispose();

            // create new
            const wb = univerRef.current.createWorkbook(state.workbook);
            wb?.getSheets()?.[0]?.activate();

            /* async formula recalculation (original code) ---------------- */
            const formula = univerRef.current.getFormula();
            if (formula) {
                formula.executeCalculation();
                formula
                    .whenComputingCompleteAsync(3000)
                    .finally(() => (isLoadingRef.current = false));

                calculationProcessingCallback.current?.dispose();
                calculationProcessingCallback.current = formula.calculationProcessing((stage) =>
                    console.log('Formula stage', stage),
                );
            }
            isLoadingRef.current = false;
        }, [state.workbook]);

        // --- Univer Initialization and Data Loading ---
        // useEffect(() => {
        //     console.log("Initializing UniverJS...");
        //     if (containerRef.current && !univerRef.current) {
        //         try {
        //             // Initialize Univer
        //             const {univerAPI} = createUniver({
        //                 locale: LocaleType.FR_FR,
        //                 locales: {[LocaleType.FR_FR]: merge({}, UniverPresetSheetsCoreFrFR, UniverPresetSheetsDataValidationFrFR)},
        //                 theme: defaultTheme,
        //                 presets: [
        //                     UniverSheetsCorePreset({
        //                         container: containerRef.current!,
        //                         ribbonType: "simple",
        //                         header: true,
        //                         toolbar: true,
        //                         contextMenu: true,
        //                         statusBarStatistic: false,
        //                     }),
        //                     UniverSheetsDataValidationPreset(),
        //                 ],
        //             });
        //
        //             univerRef.current = univerAPI;
        //             setUniverAPI(univerAPI);
        //
        //             console.log("UniverJS initialized successfully");
        //
        //             // --- Event Listener for Cell Changes ---
        //             univerAPI.addEvent(univerAPI.Event.SheetValueChanged, async (params: any) => {
        //                 if (isLoadingRef.current) return;
        //                 console.log("Started processing change message")
        //                 const payload = params.payload;
        //
        //                 if (!payload || !payload.params || !payload.params.cellValue || payload.id !== "sheet.mutation.set-range-values") {
        //                     console.warn("Invalid payload, skipping debounced processing.");
        //                     return;
        //                 }
        //
        //                 const worksheetId = payload.params.subUnitId;
        //                 const workbook = univerRef.current?.getActiveWorkbook();
        //                 if (!workbook) return;
        //
        //                 const modifiedSheet = workbook.getSheetBySheetId(worksheetId);
        //
        //                 if (!modifiedSheet) {
        //                     console.warn("Sheet not found in workbook. Skipping change.");
        //                     return;
        //                 }
        //
        //                 const originalChange = payload.params.cellValue;
        //                 const filteredChange: { [key: string]: { [key: string]: any } } = {};
        //                 let hasValidChanges = false;
        //
        //                 // This entire block is now deferred and won't block the UI
        //                 Object.entries(originalChange).forEach(([rowIndex, rowData]) => {
        //                     const rowChanges: { [key: string]: any } = {};
        //                     let rowHasValidChanges = false;
        //                     Object.entries(rowData as object).forEach(([colIndex, cellData]) => {
        //                         const cell = modifiedSheet.getRange(parseInt(rowIndex), parseInt(colIndex));
        //                         if (!cell?.getFormula()) {
        //                             rowChanges[colIndex] = cellData;
        //                             rowHasValidChanges = true;
        //                             hasValidChanges = true;
        //                         }
        //                     });
        //                     if (rowHasValidChanges) {
        //                         filteredChange[rowIndex] = rowChanges;
        //                     }
        //                 });
        //
        //                 if (!hasValidChanges) {
        //                     console.log("Debounced processing found no non-formula changes. Skipping send.");
        //                     return;
        //                 }
        //
        //                 const changeData = {
        //                     sheet: modifiedSheet.getSheetName() ?? "Unknown",
        //                     value: filteredChange,
        //                     timestamp: Date.now(),
        //                 };
        //
        //                 onCellChange(changeData);
        //             });
        //
        //         } catch (error) {
        //             console.error("Failed to initialize UniverJS:", error);
        //         }
        //     }
        //
        //     // --- Data Loading Logic ---
        //     if (univerRef.current && state.workbook) {
        //         isLoadingRef.current = true;
        //         try {
        //             console.log("Loading new IWorkbookData:", state.workbook);
        //
        //             // Dispose of the old workbook if it exists
        //             const currentWorkbook = univerRef.current.getActiveWorkbook();
        //             if (currentWorkbook) {
        //                 univerRef.current.getActiveWorkbook()?.dispose();
        //             }
        //
        //             // Create a new workbook from the provided data
        //             const newWorkbook = univerRef.current.createWorkbook(state.workbook);
        //             if (!newWorkbook) {
        //                 console.error("Failed to create workbook from data");
        //                 return;
        //             }
        //
        //             // Activate the first sheet
        //             newWorkbook.getSheets()?.[0]?.activate();
        //             console.log(`Workbook loaded successfully with ${newWorkbook.getSheets().length} sheets`);
        //
        //             setTimeout(() => {
        //                 if (!univerRef.current) {
        //                     console.log("Univer instance disposed, skipping scheduled calculation.")
        //                     return
        //                 }
        //
        //                 const formula = univerRef.current.getFormula()
        //                 if (formula) {
        //                     console.log("Starting asynchronous formula calculation...")
        //                     isLoadingRef.current = true
        //
        //                     formula.executeCalculation()
        //
        //                     formula.whenComputingCompleteAsync(3000)
        //                         .then(() => {
        //                             console.log("Asynchronous formula calculation finished.")
        //                         })
        //                         .catch((err) => {
        //                             console.error("Error during asynchronous formula calculation:", err)
        //                         })
        //                         .finally(() => {
        //                             // Always set the loading flag to false when calculation is done or has failed
        //                             isLoadingRef.current = false
        //                         })
        //                 } else {
        //                     console.warn("Formula engine not available, skipping scheduled calculation.")
        //                     isLoadingRef.current = false
        //                 }
        //             }, 3000) // 3 seconds
        //
        //             const formulaEngine = univerRef.current.getFormula();
        //             calculationProcessingCallback.current = formulaEngine.calculationProcessing((stageInfo) => {
        //                 console.log('Calculation processing', stageInfo);
        //             })
        //
        //         } catch (error) {
        //             console.error("Error loading workbook data:", error);
        //         }
        //     }
        //
        //     // --- Cleanup on component unmount ---
        //     return () => {
        //         if (calculationProcessingCallback.current) {
        //             calculationProcessingCallback.current.dispose();
        //         }
        //         univerRef.current?.dispose();
        //         univerRef.current = null;
        //     };
        // }, [state.workbook, onCellChange]); // Re-run effect if initialData or callbacks change

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