import { useState, useEffect } from 'react';
import { useWorkbook } from '../ExcelViewer/WorkbookContext';
import { applyOpsToUniver, rollbackOperation, clearOperationHistory } from "../Helpers/applyOpsToUniver.tsx";
import { getUniverAPI } from '../ExcelViewer/UniverInstance';
import type { Operation } from '../Shared/Contract';
import './ValidationToolbar.css';

interface Props {
  ws: WebSocket | null;
}

type ValidationStatus = 'pending' | 'accepted' | 'refused';

interface ValidationItem {
  operation: Operation;
  status: ValidationStatus;
  originalState?: any; // Store original state for rollback
}

export default function ValidationToolbar({ ws }: Props) {
  const {
    state: { pendingOps },
    dispatch,
  } = useWorkbook();

  const [validations, setValidations] = useState<ValidationItem[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Initialize validations when pendingOps change
  useEffect(() => {
    const newValidations = pendingOps.map(op => ({
      operation: op,
      status: 'pending' as ValidationStatus,
    }));
    setValidations(newValidations);

    // Apply all operations initially (can be rolled back later)
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
        const { sheet, row, col } = op.payload as any;
        const targetSheet = wb.getSheetByName(sheet);
        if (targetSheet) {
          wb.setActiveSheet(targetSheet);
          targetSheet.getRange(row, col).activate();
        }
        break;
      }
      case 'CREATE_SHEET':
      case 'DELETE_SHEET': {
        const { sheet_name } = op.payload as any;
        const targetSheet = wb.getSheetByName(sheet_name);
        if (targetSheet) {
          wb.setActiveSheet(targetSheet);
        }
        break;
      }
      case 'REPLACE_SHEET': {
        const worksheetData = op.payload as any;
        const targetSheet = wb.getSheetByName(worksheetData.name);
        if (targetSheet) {
          wb.setActiveSheet(targetSheet);
        }
        break;
      }
    }
  };

  const updateStatus = (index: number, status: ValidationStatus) => {
    setValidations(prev => {
      const updated = [...prev];
      const item = updated[index];

      // If changing from accepted to refused or vice versa, we need to handle the operation
      if (item.status === 'accepted' && status === 'refused') {
        // Rollback the operation
        handleRollback(item.operation);
      } else if (item.status === 'refused' && status === 'accepted') {
        // Apply the operation
        applyOpsToUniver([item.operation]);
      }

      updated[index] = { ...item, status };
      return updated;
    });
  };

  const handleRollback = (op: Operation) => {
    const success = rollbackOperation(op);
    if (!success) {
      console.error('Failed to rollback operation:', op);
    }
  };

  const acceptAll = () => {
    setValidations(prev => prev.map(v => ({ ...v, status: 'accepted' })));
  };

  const refuseAll = () => {
    setValidations(prev => prev.map(v => ({ ...v, status: 'refused' })));
    // Rollback all operations
    validations.forEach(v => {
      if (v.status !== 'refused') {
        handleRollback(v.operation);
      }
    });
  };

  const canConfirm = validations.every(v => v.status !== 'pending');

  const handleConfirm = () => {
    if (!canConfirm || !ws) return;

    const acceptedIds = validations
      .filter(v => v.status === 'accepted')
      .map(v => v.operation.id);

    const refusedIds = validations
      .filter(v => v.status === 'refused')
      .map(v => v.operation.id);

    // Send validation results to backend
    ws.send(JSON.stringify({
      type: 'validate_changes',
      payload: {
        accepted: acceptedIds,
        refused: refusedIds
      }
    }));

    // Clear operation history for all processed operations
    clearOperationHistory(validations.map(v => v.operation.id));

    // Clear pending operations
    dispatch({ type: 'CLEAR_PENDING' });
    setValidations([]);
  };

  const getStatusColor = (status: ValidationStatus) => {
    switch (status) {
      case 'accepted': return '#28a745';
      case 'refused': return '#dc3545';
      case 'pending': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getOperationDescription = (op: Operation) => {
    switch (op.type) {
      case 'UPDATE_CELL': {
        const { sheet, row, col, value } = op.payload as any;
        return `Cell Update: ${sheet} [${row},${col}] = ${value?.v || ''}`;
      }
      case 'CREATE_SHEET': {
        const { sheet_name } = op.payload as any;
        return `Create Sheet: ${sheet_name}`;
      }
      case 'DELETE_SHEET': {
        const { sheet_name } = op.payload as any;
        return `Delete Sheet: ${sheet_name}`;
      }
      case 'REPLACE_SHEET': {
        const worksheetData = op.payload as any;
        return `Replace Sheet: ${worksheetData.name}`;
      }
      default:
        return op.description || `Operation: ${op.type}`;
    }
  };

  return (
    <div className="validation-toolbar">
      <div className="toolbar-header">
        <h3>Pending Validations ({validations.length})</h3>
        <div className="toolbar-actions">
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
            className={`validation-item ${selectedIndex === index ? 'selected' : ''}`}
            onClick={() => handleValidationClick(index, item)}
          >
            <div
              className="status-indicator"
              style={{ backgroundColor: getStatusColor(item.status) }}
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
                  title="Accept"
                >
                  ✓
                </button>
                <button
                  className={`action-btn refuse ${item.status === 'refused' ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    updateStatus(index, 'refused');
                  }}
                  title="Refuse"
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