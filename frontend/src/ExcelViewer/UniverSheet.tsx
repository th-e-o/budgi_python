import {
    createUniver,
    defaultTheme,
    FUniver,
    LocaleType,
    merge, Univer,
} from "@univerjs/presets";
import {
    CalculationMode, UniverSheetsCorePreset,
    type IBeforeSheetEditStartEventParams, type ISetRangeValuesMutationParams, type ISheetValueChangedEvent
} from "@univerjs/presets/preset-sheets-core";
import UniverPresetSheetsCoreFrFR from "@univerjs/presets/preset-sheets-core/locales/fr-FR";
import {UniverSheetsDataValidationPreset} from "@univerjs/presets/preset-sheets-data-validation";
import UniverPresetSheetsDataValidationFrFR from "@univerjs/presets/preset-sheets-data-validation/locales/fr-FR";
import "@univerjs/presets/lib/styles/preset-sheets-core.css";
import "@univerjs/presets/lib/styles/preset-sheets-data-validation.css";

import {forwardRef, useEffect, useImperativeHandle, useRef} from "react";
import {type IDisposable, type IWorkbookData} from "@univerjs/core";
import type {Operation} from "../types/contract.tsx";
import {applyOpsToUniver, isApplyingProgrammaticChange} from "../Helpers/applyOpsToUniver.tsx";
import {setUniverAPI} from "./UniverInstance.tsx";
import {useWorkbook} from "./WorkbookContext.tsx";
import {IRenderManagerService} from "@univerjs/engine-render";
import {AnimatedFlashObject} from "./ChangeDisallowedExtension.tsx";

export interface UniverSheetHandle {
    applyOperations: (ops: Operation[]) => void;
    recalculateFormulas: () => void;
}

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
        const univerInstanceRef = useRef<Univer | null>(null);
        const loadedPointer = useRef<IWorkbookData | null>(null);
        const isUserEditAllowedRef = useRef<boolean>(true);

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
        const isValidationPendingRef = useRef<boolean>(false);

        // Track if we are currently processing a validation operation or loading data to prevent user edits
        useEffect(() => {
            const isPending = state.pendingOps.length > 0;
            const isLoading = isLoadingRef.current;
            isUserEditAllowedRef.current = !isPending && !isLoading;
        }, [state.pendingOps]);

        useEffect(() => {
            if (!containerRef.current || univerApiRef.current) return;

            const {univer, univerAPI} = createUniver({
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
            univerInstanceRef.current = univer;

            setUniverAPI(univerAPI);

            const disposables: IDisposable[] = [];
            const formula = univerAPI.getFormula();

            disposables.push(formula.calculationEnd(() => {
                onCalculationEnd?.();
            }));

            disposables.push(formula.calculationStart((forceCalculation) => {
                const currentFormula = univerApiRef.current?.getFormula();
                if (forceCalculation) {
                    console.log("Manual calculation has started with force calculation.");
                } else {
                    console.log("Canceling automatic calculation as it was not forced.");
                    currentFormula?.stopCalculation();
                }
            }));

            disposables.push(
                univerAPI.addEvent(univerAPI.Event.BeforeSheetEditStart, (params: IBeforeSheetEditStartEventParams) => {
                    if (!isUserEditAllowedRef.current) {
                        params.cancel = true; // Prevent the edit

                        const core = univerInstanceRef.current;
                        if (!core) return;

                        const workbook = univerAPI.getActiveWorkbook();
                        const worksheet = workbook?.getActiveSheet();
                        const renderManager = core.__getInjector().get(IRenderManagerService);
                        const renderUnit = renderManager.getRenderById(workbook!.getId());
                        const mainComponent = renderUnit?.mainComponent;
                        const scene = renderUnit?.scene;
                        const skeleton = worksheet?.getSkeleton();

                        if (!scene || !skeleton || !mainComponent) return;

                        const { startX, startY, endX, endY } = skeleton.getCellWithCoordByIndex(params.row, params.column);

                        const animationDuration = 500; // Duration in milliseconds
                        const flashObject = new AnimatedFlashObject(
                            `flash-${Date.now()}`,
                            {
                                left: startX,
                                top: startY,
                                width: endX - startX,
                                height: endY - startY,
                                initialColor: [255, 0, 0], // Red
                                duration: 500, // Animate for 500ms
                                zIndex: 60,
                                evented: false,
                            }
                        );

                        scene.addObject(flashObject);

                        const animationStartTime = Date.now();

                        const animate = () => {
                            const elapsedTime = Date.now() - animationStartTime;

                            // Force a repaint on each frame
                            mainComponent.makeDirty(true);

                            // Continue the loop until the animation is done
                            if (elapsedTime < animationDuration) {
                                requestAnimationFrame(animate);
                            }
                        };

                        // Kick off the first frame
                        requestAnimationFrame(animate);
                    }
                })
            );

            /* --- Cell-change listener ------------------------ */
            disposables.push(univerAPI.addEvent(univerAPI.Event.SheetValueChanged, async (params: ISheetValueChangedEvent) => {
                if (isApplyingProgrammaticChange()) return;
                if (isLoadingRef.current) return;
                if (isValidationPendingRef.current) return; // skip if there are pending ops
                console.log("Started processing change message")
                const payload = params.payload;
                const payloadParams = payload.params as ISetRangeValuesMutationParams;

                if (!payload || !payloadParams || !payloadParams.cellValue || payload.id !== "sheet.mutation.set-range-values") {
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

                // @ts-expect-error - TS doesn't recognize the debounce function
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

                console.log("Sending debounced change:", filteredChange);

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