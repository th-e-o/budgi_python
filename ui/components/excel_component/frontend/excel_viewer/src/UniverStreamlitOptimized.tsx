import {
	createUniver,
	defaultTheme,
	FUniver,
	LocaleType,
	merge,
} from "@univerjs/presets"
import { UniverSheetsCorePreset } from "@univerjs/presets/preset-sheets-core"
import UniverPresetSheetsCoreFrFR from "@univerjs/presets/preset-sheets-core/locales/fr-FR"
import { UniverSheetsDataValidationPreset } from "@univerjs/presets/preset-sheets-data-validation"
import UniverPresetSheetsDataValidationFrFR from "@univerjs/presets/preset-sheets-data-validation/locales/fr-FR"

import "@univerjs/presets/lib/styles/preset-sheets-core.css"
import "@univerjs/presets/lib/styles/preset-sheets-data-validation.css"
import "./UniverSheet.css"

import {
	type ComponentProps,
	Streamlit,
	withStreamlitConnection,
} from "streamlit-component-lib"

import React, { useEffect, useRef, useCallback, useState } from "react"

const UniverStreamlitComponent: React.FC<ComponentProps> = (props) => {
	const [containerHeight, setContainerHeight] = useState(props.args.height || 600)
	const wrapperRef = useRef<HTMLDivElement>(null)
	const univerContainerRef = useRef<HTMLDivElement>(null)
	const univerInstanceRef = useRef<FUniver | null>(null)
	const isLoadingRef = useRef<boolean>(false)

	const { initial_data: initialData, update_command: updateCommand } = props.args
	const isInitializedRef = useRef<boolean>(false)

	// Initial data import
	const loadJsonData = useCallback(async (workbookData: any) => {
		if (!univerInstanceRef.current) return
		isLoadingRef.current = true

		try {
			console.log("Loading IWorkbookData:", workbookData)

			const currentWorkbook = univerInstanceRef.current.getActiveWorkbook()
			if (currentWorkbook) {
				// Dispose of the current workbook
				const workbookId = currentWorkbook.getId()
				univerInstanceRef.current.getWorkbook(workbookId)?.dispose()
			}

			// Create new workbook with the complete IWorkbookData structure
			const definedNames = workbookData.definedNames;
			delete workbookData.definedNames
			let newWorkbook = univerInstanceRef.current.createWorkbook(workbookData)

			if (!newWorkbook) {
				console.error("Failed to create workbook from data")
				return
			}

			definedNames.forEach((o: any) =>{
				console.log(o.n)
				console.log(o.formulaRefOrString)
				newWorkbook = newWorkbook.insertDefinedName(o.n, o.formulaRefOrString);
			})

			console.log("Successfully loaded workbook, starting calculation in 3 seconds")
			setTimeout(() => {
				if (!univerInstanceRef.current) {
					console.log("Univer instance disposed, skipping scheduled calculation.")
					return
				}

				const formula = univerInstanceRef.current.getFormula()
				if (formula) {
					console.log("Starting asynchronous formula calculation...")
					isLoadingRef.current = true

					formula.executeCalculation()

					formula.whenComputingCompleteAsync()
						.then(() => {
							console.log("Asynchronous formula calculation finished.")
						})
						.catch((err: any) => {
							console.error("Error during asynchronous formula calculation:", err)
						})
						.finally(() => {
							// Always set the loading flag to false when calculation is done or has failed
							isLoadingRef.current = false
						})
				} else {
					console.warn("Formula engine not available, skipping scheduled calculation.")
				}
			}, 3000) // 3000ms = 3 seconds

			// Activate the first sheet
			const sheets = newWorkbook.getSheets()
			if (sheets && sheets.length > 0) {
				sheets[0].activate()
			}

			console.log(`Workbook loaded successfully with ${sheets?.length || 0} sheets`)
		} catch (error) {
			console.error("Error loading workbook data:", error)
		} finally {
			isLoadingRef.current = false
		}
	}, [])

	// Update processing
	const processUpdateCommand = useCallback((command: any) => {
		if (!univerInstanceRef.current || !command || !command.action) return

		console.log("Processing command from Streamlit:", command)
		isLoadingRef.current = true // Prevent user edits during programmatic update
		try {
			const fWorkbook = univerInstanceRef.current.getActiveWorkbook()
			if (!fWorkbook) return

			if (command.action === "update_cells" && command.payload) {
				command.payload.forEach((update: any) => {
					const { sheet: sheetName, cell: cellAddress, value, value_type: valueType } = update
					const fWorksheet = fWorkbook.getSheetByName(sheetName)
					if (fWorksheet) {
						const range = fWorksheet.getRange(cellAddress)
						if (valueType === "f") range.setFormula(value)
						else range.setValue(value)

					} else {
						console.warn(`Sheet "${sheetName}" not found for update command.`)
					}
				})
			}

		} catch (error) {
			console.error("Error processing update command:", error)
		} finally {
			isLoadingRef.current = false
		}
	}, [])

	// --- Lifecycle Effects ---
	useEffect(() => {
		if (univerContainerRef.current && !univerInstanceRef.current) {
			try {
				const { univerAPI } = createUniver({
					locale: LocaleType.FR_FR,
					locales: { [LocaleType.FR_FR]: merge({}, UniverPresetSheetsCoreFrFR, UniverPresetSheetsDataValidationFrFR) },
					theme: defaultTheme,
					presets: [
						UniverSheetsCorePreset({
							container: univerContainerRef.current,
							ribbonType: "simple", header: true, toolbar: true, contextMenu: true,
							statusBarStatistic: false,
						}),
						UniverSheetsDataValidationPreset(),
					],
				})

				univerInstanceRef.current = univerAPI
				console.log("UniverJS initialized successfully")

				univerAPI.addEvent(univerAPI.Event.SheetValueChanged, (params: any) => {
					if (isLoadingRef.current) return
					console.log(params)
					const payload = params.payload

					if (!payload || !payload.params || !payload.params.cellValue || payload.id !== "sheet.mutation.set-range-values") {
						return
					}
					const originalChange = payload.params.cellValue
					const filteredChange: { [key: string]: { [key: string]: any } } = {}
					let hasValidChanges = false

					Object.entries(originalChange).forEach(([rowIndex, rowData]) => {
						const rowChanges: { [key: string]: any } = {}
						let rowHasValidChanges = false

						Object.entries(rowData as object).forEach(([colIndex, cellData]) => {
							// Check if the cell data for this specific cell is a formula
							const cell = univerInstanceRef.current?.getActiveSheet()?.worksheet.getRange(parseInt(rowIndex), parseInt(colIndex))
							const formula = cell?.getFormula()
							console.log(formula)
							if (formula && formula !== "") {
								return
							}

							if (cellData && (cellData.f === undefined || cellData.f === null)) {
								rowChanges[colIndex] = cellData
								rowHasValidChanges = true
								hasValidChanges = true
							}
						})

						if (rowHasValidChanges) {
							filteredChange[rowIndex] = rowChanges
						}
					})

					if (!hasValidChanges) {
						console.log("All changes were formula edits. Not sending to Streamlit.")
						return
					}

					const cellAddress = params.effectedRanges?.[0]?.getA1Notation()
					const changeData = {
						sheet: univerInstanceRef.current?.getActiveSheet()?.worksheet.getSheetName() ?? "Unknown",
						range: cellAddress,
						value: filteredChange, // Send the CLEANED/FILTERED object
						timestamp: Date.now(),
					}

					console.log("Sending FILTERED change to Streamlit:", changeData)
					Streamlit.setComponentValue(changeData)
				})

			} catch (error) {
				console.error("Failed to initialize UniverJS:", error)
			}
		}

		Streamlit.setComponentReady()

		return () => {
			univerInstanceRef.current?.dispose()
			univerInstanceRef.current = null
		}
	}, [])

	useEffect(() => {
		if (initialData && !isInitializedRef.current) {
			loadJsonData(initialData)
			isInitializedRef.current = true
		}

		// --- COMMAND PROCESSING ---
		if (updateCommand) {
			processUpdateCommand(updateCommand)
			// Tell Streamlit we've processed the command by setting the component value to null
			Streamlit.setComponentValue(null)
		}
	}, [initialData, updateCommand, loadJsonData, processUpdateCommand])

	// --- Rendering ---
	useEffect(() => {
		const wrapper = wrapperRef.current
		if (!wrapper) return

		const resizeObserver = new ResizeObserver((entries) => {
			const entry = entries[0]
			if (entry) {
				const newHeight = entry.contentRect.height

				// Calculate the inner height, ensuring it doesn't go below a minimum value
				const innerHeight = newHeight > 20 ? newHeight - 10 : 200

				// Update our state with the new height
				setContainerHeight(innerHeight)
			}
		})

		resizeObserver.observe(wrapper)
		return () => {
			resizeObserver.disconnect()
		}
	}, [])


	return (
	  // This is the outer wrapper div which will fill the available space.
	  <div
		ref={wrapperRef}
		style={{
			width: "100%",
			height: `${props.args.height || 600}px`,
			position: "relative",
		}}
	  >
		  {/* This is the INNER div that UniverJS will attach to. */}
		  <div
			ref={univerContainerRef}
			className="univer-sheet-container"
			style={{
				width: "100%",
				height: `${containerHeight}px`,
				border: "1px solid #ccc",
				borderRadius: "4px",
			}}
		  />
	  </div>
	)
}

export default withStreamlitConnection(UniverStreamlitComponent)