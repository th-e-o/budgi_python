import {
	BorderType,
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

const borderSideMap: { [key: string]: BorderType } = {
	left: BorderType.LEFT,
	right: BorderType.RIGHT,
	top: BorderType.TOP,
	bottom: BorderType.BOTTOM,
}

const UniverStreamlitComponent: React.FC<ComponentProps> = (props) => {
	const [containerHeight, setContainerHeight] = useState(props.args.height || 600)
	const wrapperRef = useRef<HTMLDivElement>(null)
	const univerContainerRef = useRef<HTMLDivElement>(null)
	const univerInstanceRef = useRef<FUniver | null>(null)
	const isLoadingRef = useRef<boolean>(false)

	const { initial_data: initialData, update_command: updateCommand } = props.args
	const isInitializedRef = useRef<boolean>(false)

	const convertColumnWidth = (openpyxlWidth: number): number => Math.round(openpyxlWidth * 8.5)
	const convertRowHeight = (openpyxlHeight: number): number => Math.round(openpyxlHeight * (100 / 72))

	// Initial data import
	const loadJsonData = useCallback((sheetData: any) => {
		if (!univerInstanceRef.current) return
		isLoadingRef.current = true

		try {
			console.log("Loading JSON data:", sheetData)
			const fWorkbook = univerInstanceRef.current.getActiveWorkbook()
			if (!fWorkbook) {
				console.error("Workbook not found. Cannot load data.")
				return
			}
			const existingSheets = fWorkbook.getSheets()

			const sheetNames = Object.keys(sheetData)
			if (!sheetNames || sheetNames.length === 0) {
				return
			}

			//await sleep(50)

			sheetNames.forEach((sheetName) => {
				const sheet = sheetData[sheetName]
				console.log(`Processing sheet: ${sheetName}`)

				const [maxRows, maxCols] = sheet.dimensions || [100, 26]
				const fWorksheet = fWorkbook.create(sheetName, maxRows, maxCols)

				if (sheet.rowHeights) {
					Object.entries(sheet.rowHeights).forEach(([rowNum, height]) => {
						try {
							fWorksheet.setRowHeightsForced(parseInt(rowNum) - 1, 1, convertRowHeight(height as number))
						} catch (error) {
							console.warn(`Failed to set row height for row ${rowNum}:`, error)
						}
					})
				}
				if (sheet.columnWidths) {
					Object.entries(sheet.columnWidths).forEach(([colLetter, width]) => {
						try {
							const colIndex = colLetter.charCodeAt(0) - 65
							fWorksheet.setColumnWidth(colIndex, convertColumnWidth(width as number))
						} catch (error) {
							console.warn(`Failed to set column width for column ${colLetter}:`, error)
						}
					})
				}

				if (sheet.hiddenGridLines){
					try {
						fWorksheet.setHiddenGridlines(sheet.hiddenGridLines)
					} catch (error) {
						console.warn(`Failed to set grid lines for sheet ${sheetName}:`, error)
					}
				}

				if (sheet.valuesWithTypes){
					Object.keys(sheet.valuesWithTypes).forEach((coordinate) => {
						const valueAndTypes = sheet.valuesWithTypes[coordinate]
						const value = valueAndTypes.value
						const type = valueAndTypes.type
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (value !== null && value !== undefined) {
								if (type !== "f") {
									univerCell.setValue(value)
								}
							}
						} catch (error) {
							console.warn(`Failed to set value for cell ${coordinate}:`, error, { type, value })
						}
					})
				}

				if (sheet.bgColor){
					Object.keys(sheet.bgColor).forEach((coordinate) => {
						const bgColor = sheet.bgColor[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (bgColor) {
								univerCell.setBackground(bgColor.startsWith("#") ? bgColor : `#${bgColor}`)
							}
						} catch (error) {
							console.warn(`Failed to set background color for cell ${coordinate}:`, error, bgColor)
						}
					})
				}

				if (sheet.fontBold){
					Object.keys(sheet.fontBold).forEach((coordinate) => {
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							univerCell.setFontWeight("bold")
						} catch (error) {
							console.warn(`Failed to set font weight for cell ${coordinate}:`, error)
						}
					})
				}

				if (sheet.fontItalic){
					Object.keys(sheet.fontItalic).forEach((coordinate) => {
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							univerCell.setFontStyle("italic")
						} catch (error) {
							console.warn(`Failed to set font style for cell ${coordinate}:`, error)
						}
					})
				}

				if (sheet.fontUnderline){
					Object.keys(sheet.fontUnderline).forEach((coordinate) => {
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							univerCell.setFontLine("underline")
						} catch (error) {
							console.warn(`Failed to set font underline for cell ${coordinate}:`, error)
						}
					})
				}

				if (sheet.fontSize){
					Object.keys(sheet.fontSize).forEach((coordinate) => {
						const fontSize = sheet.fontSize[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (fontSize) {
								univerCell.setFontSize(fontSize)
							}
						} catch (error) {
							console.warn(`Failed to set font size for cell ${coordinate}:`, error, fontSize)
						}
					})
				}

				if (sheet.fontColor){
					Object.keys(sheet.fontColor).forEach((coordinate) => {
						const fontColor = sheet.fontColor[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (fontColor) {
								univerCell.setFontColor(fontColor.startsWith("#") ? fontColor : `#${fontColor}`)
							}
						} catch (error) {
							console.warn(`Failed to set font color for cell ${coordinate}:`, error, fontColor)
						}
					})
				}

				if (sheet.fontName){
					Object.keys(sheet.fontName).forEach((coordinate) => {
						const fontName = sheet.fontName[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (fontName) {
								univerCell.setFontFamily(fontName)
							}
						} catch (error) {
							console.warn(`Failed to set font name for cell ${coordinate}:`, error, fontName)
						}
					})
				}

				if (sheet.alignHorizontal) {
					Object.keys(sheet.alignHorizontal).forEach((coordinate) => {
						const alignHorizontal = sheet.alignHorizontal[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (alignHorizontal) {
								univerCell.setHorizontalAlignment(alignHorizontal === "right" ? "normal" : alignHorizontal)
							}
						} catch (error) {
							console.warn(`Failed to set horizontal alignment for cell ${coordinate}:`, error, alignHorizontal)
						}
					})
				}

				if (sheet.alignVertical) {
					Object.keys(sheet.alignVertical).forEach((coordinate) => {
						const alignVertical = sheet.alignVertical[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (alignVertical) {
								univerCell.setVerticalAlignment(alignVertical === "center" ? "middle" : alignVertical)
							}
						} catch (error) {
							console.warn(`Failed to set vertical alignment for cell ${coordinate}:`, error, alignVertical)
						}
					})
				}

				if (sheet.wrapText) {
					Object.keys(sheet.wrapText).forEach((coordinate) => {
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							univerCell.setWrap(true)
						} catch (error) {
							console.warn(`Failed to set wrap text for cell ${coordinate}:`, error)
						}
					})
				}

				if (sheet.borders){
					Object.keys(sheet.borders).forEach((coordinate) => {
						const borders = sheet.borders[coordinate]
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (borders) {
								Object.keys(borders).forEach((side) => {
									const borderData = borders[side]
									if (borderData && borderData.style && borderData.style !== "none" && borderSideMap[side]) {
										try {
											univerCell.setBorder(
												borderSideMap[side],
												borderData.style.toUpperCase(),
												borderData.color ? (borderData.color.startsWith("#") ? borderData.color : `#${borderData.color}`) : "#000000"
											)
										} catch (e) {
											console.warn(`Failed to apply ${side} border:`, e)
										}
									}
								})
							}
						} catch (error) {
							console.warn(`Failed to set borders for cell ${coordinate}:`, error, borders)
						}
					})
				}
			})

			sheetNames.forEach((sheetName) => {
				const sheet = sheetData[sheetName]
				console.log(`Processing sheet: ${sheetName}`)

				const fWorksheet = fWorkbook.getSheetByName(sheetName)

				if (sheet.valuesWithTypes) {
					Object.keys(sheet.valuesWithTypes).forEach((coordinate) => {
						const valueAndTypes = sheet.valuesWithTypes[coordinate]
						const value = valueAndTypes.value
						const type = valueAndTypes.type
						if (!fWorksheet) {
							return
						}
						try {
							const univerCell = fWorksheet.getRange(coordinate)
							if (value !== null && value !== undefined) {
								if (type === "f") {
									univerCell.setFormula(value)
								}
							}
						} catch (error) {
							console.warn(`Failed to set value for cell ${coordinate}:`, error, { type, value })
						}
					})
				}
			})

			setTimeout(() => {
				if (!univerInstanceRef.current) return // Guard against component unmount

				const fWorkbook = univerInstanceRef.current.getActiveWorkbook()
				if (!fWorkbook) return

				console.log("Executing deferred merge operations...")
				sheetNames.forEach((sheetName) => {
					const sheet = sheetData[sheetName]
					const fWorksheet = fWorkbook.getSheetByName(sheetName)

					if (fWorksheet && sheet.mergedRanges) {
						sheet.mergedRanges.forEach((mergeRange: string) => {
							try {
								fWorksheet.getRange(mergeRange).merge(true)
							} catch (error) {
								console.warn(`Failed to merge range ${mergeRange}:`, error)
							}
						})
					}
				})

				// Activate the first sheet after merges are done.
				const firstSheet = fWorkbook.getSheets()[0]
				if (firstSheet) {
					firstSheet.activate()
				}

				console.log("Deferred operations complete.")
				// All loading is now truly finished.
				isLoadingRef.current = false

			}, 0) // A delay of 0ms is enough to push it to the next event loop tick.


			// Delete sheets
			for (let i = existingSheets.length - 1; i >= 0; i--) {
				fWorkbook.deleteSheet(existingSheets[i].getSheetId())
			}
			console.log("Finished deleting old sheets.")

			const firstSheet = fWorkbook.getSheets()[0]
			if (firstSheet) firstSheet.activate()

			console.log(`JSON data loaded successfully with ${sheetNames.length} sheets`)
		} catch (error) {
			console.error("Error loading JSON data:", error)
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

				univerAPI.createWorkbook({ name: "Streamlit Sheet" })

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

					// The change object is a dictionary of rows, which contains a dictionary of columns.
					// e.g., { '0': { '1': { v: 'hello' } }, '2': { '3': { f: '=A1', v: 'val' } } }
					Object.entries(originalChange).forEach(([rowIndex, rowData]) => {
						const rowChanges: { [key: string]: any } = {}
						let rowHasValidChanges = false

						Object.entries(rowData as object).forEach(([colIndex, cellData]) => {
							// Check if the cell data for this specific cell is a formula
							const cell = univerInstanceRef.current?.getActiveSheet()?.worksheet.getRange(parseInt(rowIndex), parseInt(colIndex))
							const formula = cell?.getFormula()
							console.log(formula)
							if (cell && formula && formula.startsWith("=")) {
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