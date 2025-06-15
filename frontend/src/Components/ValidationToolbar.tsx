import {useState, useEffect} from 'react';
import {useWorkbook} from '../ExcelViewer/WorkbookContext';
import {applyOpsToUniver, rollbackOperation, clearOperationHistory} from "../Helpers/applyOpsToUniver.tsx";
import {getUniverAPI} from '../ExcelViewer/UniverInstance';
import type {Operation} from '../types/contract.tsx';
import './ValidationToolbar.css';

interface Props {
    onConfirm: (acceptedIds: string[], refusedIds: string[]) => void;
}

type ValidationStatus = 'pending' | 'accepted' | 'refused';

interface ValidationItem {
    operation: Operation;
    status: ValidationStatus;
    applied: boolean; // Track whether this operation has been applied
}

export default function ValidationToolbar({onConfirm}: Props) {
    const {
        state: {pendingOps},
        dispatch,
    } = useWorkbook();

    const [validations, setValidations] = useState<ValidationItem[]>([]);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

    // Initialize validations when pendingOps change
    useEffect(() => {
        const newValidations = pendingOps.map(op => ({
            operation: op,
            status: 'pending' as ValidationStatus,
            applied: true, // Operations are applied immediately for preview
        }));
        setValidations(newValidations);

        // Apply all operations immediately when they arrive
        if (pendingOps.length > 0) {
            applyOpsToUniver(pendingOps);
        }
    }, [pendingOps]);

    if (validations.length === 0) return null;

    const handleValidationClick = (index: number, item: ValidationItem) => {
        setSelectedIndex(index);

        // Scroll to the relevant cell based on operation type
        const univer = getUniverAPI();
        if (!univer) return;

        const wb = univer.getActiveWorkbook();
        if (!wb) return;

        const op = item.operation;

        switch (op.type) {
            case 'UPDATE_CELL': {
                const {sheet, row, col} = op.payload;
                const targetSheet = wb.getSheetByName(sheet);
                if (targetSheet) {
                    wb.setActiveSheet(targetSheet);
                    targetSheet.getRange(row, col).activate();
                }
                break;
            }
            case 'CREATE_SHEET':
            case 'DELETE_SHEET': {
                const {sheet_name} = op.payload;
                const targetSheet = wb.getSheetByName(sheet_name);
                if (targetSheet) {
                    wb.setActiveSheet(targetSheet);
                }
                break;
            }
            case 'REPLACE_SHEET': {
                const worksheetData = op.payload;
                const targetSheet = wb.getSheetByName(worksheetData.name);
                if (targetSheet) {
                    wb.setActiveSheet(targetSheet);
                }
                break;
            }
        }
    };

    const updateStatus = (index: number, newStatus: ValidationStatus) => {
        setValidations(prev => {
            const updated = [...prev];
            const item = updated[index];

            // Handle state transitions
            if (newStatus === "refused" && item.applied) {
                // Rollback the operation when refusing
                const success = rollbackOperation(item.operation);
                if (success) {
                    item.applied = false;
                } else {
                    console.error('Failed to rollback operation:', item.operation);
                    // Don't update status if rollback failed
                    return prev;
                }
            } else if (newStatus === 'accepted' && !item.applied) {
                // Re-apply if it was previously refused
                applyOpsToUniver([item.operation]);
                item.applied = true;
            }

            // Update the status
            item.status = newStatus;
            updated[index] = {...item};
            return updated;
        });
    };

    const acceptAll = () => {
        setValidations(prev => {
            const updated = [...prev];
            updated.forEach((item) => {
                if (item.status !== 'accepted') {
                    if (!item.applied) {
                        applyOpsToUniver([item.operation]);
                        item.applied = true;
                    }
                    item.status = 'accepted';
                }
            });
            return updated;
        });
    };

    const refuseAll = () => {
        setValidations(prev => {
            const updated = [...prev];
            updated.forEach((item) => {
                if (item.status !== 'refused') {
                    if (item.applied) {
                        rollbackOperation(item.operation);
                        item.applied = false;
                    }
                    item.status = 'refused';
                }
            });
            return updated;
        });
    };

    const canConfirm = validations.every(v => v.status !== 'pending');

    const handleConfirm = () => {
        if (!canConfirm) return;

        const acceptedIds = validations
            .filter(v => v.status === 'accepted')
            .map(v => v.operation.id);

        const refusedIds = validations
            .filter(v => v.status === 'refused')
            .map(v => v.operation.id);

        // Call the callback prop
        onConfirm(acceptedIds, refusedIds);

        // This local state management can remain
        clearOperationHistory(validations.map(v => v.operation.id));
        dispatch({type: 'CLEAR_PENDING'});
        setValidations([]);
    };

    const getStatusColor = (status: ValidationStatus) => {
        switch (status) {
            case 'accepted':
                return '#28a745';
            case 'refused':
                return '#dc3545';
            case 'pending':
                return '#ffc107';
            default:
                return '#6c757d';
        }
    };

    const getOperationDescription = (op: Operation) => {
        switch (op.type) {
            case 'UPDATE_CELL': {
                const {sheet, row, col, value} = op.payload;
                return `Cell Update: ${sheet} [${row},${col}] = ${value?.v || ''}`;
            }
            case 'CREATE_SHEET': {
                const {sheet_name} = op.payload;
                return `Create Sheet: ${sheet_name}`;
            }
            case 'DELETE_SHEET': {
                const {sheet_name} = op.payload;
                return `Delete Sheet: ${sheet_name}`;
            }
            case 'REPLACE_SHEET': {
                const worksheetData = op.payload;
                return `Replace Sheet: ${worksheetData.name}`;
            }
            default: {
                op = op as any;
                return op.description || `Operation: ${op.type}`;
            }

        }
    };

    return (
        <div className="validation-toolbar">
            <div className="toolbar-header">
                <h3>Pending Validations ({validations.length})</h3>
                <div className="toolbar-actions">
                    <span className="toolbar-hint">Click items to navigate • Accept to apply changes</span>
                    <button
                        className="bulk-action-btn accept-all"
                        onClick={acceptAll}
                    >
                        ✓ Accept All
                    </button>
                    <button
                        className="bulk-action-btn refuse-all"
                        onClick={refuseAll}
                    >
                        ✗ Refuse All
                    </button>
                    <button
                        className="confirm-btn"
                        onClick={handleConfirm}
                        disabled={!canConfirm}
                    >
                        Confirm Changes
                    </button>
                </div>
            </div>

            <div className="validations-list">
                {validations.map((item, index) => (
                    <div
                        key={item.operation.id}
                        className={`validation-item ${selectedIndex === index ? 'selected' : ''} ${item.applied ? 'applied' : ''}`}
                        onClick={() => handleValidationClick(index, item)}
                    >
                        <div
                            className="status-indicator"
                            style={{backgroundColor: getStatusColor(item.status)}}
                        />
                        <div className="validation-content">
              <span className="validation-description">
                {getOperationDescription(item.operation)}
              </span>
                            <div className="validation-actions">
                                <button
                                    className={`action-btn accept ${item.status === 'accepted' ? 'active' : ''}`}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        updateStatus(index, 'accepted');
                                    }}
                                    title={item.applied ? "Operation applied" : "Accept and apply this change"}
                                >
                                    ✓
                                </button>
                                <button
                                    className={`action-btn refuse ${item.status === 'refused' ? 'active' : ''}`}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        updateStatus(index, 'refused');
                                    }}
                                    title={item.applied ? "Refuse and rollback this change" : "Refuse this change"}
                                >
                                    ✗
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}