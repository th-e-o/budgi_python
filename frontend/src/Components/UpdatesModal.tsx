import { useWorkbook } from '../ExcelViewer/WorkbookContext';
import { applyOpsToUniver } from "../Helpers/applyOpsToUniver.tsx";

interface Props {
  ws: WebSocket | null;
}

export default function UpdatesModal({ ws }: Props) {
  const {
    state: { pendingOps },
    dispatch,
  } = useWorkbook();

  if (pendingOps.length === 0) return null;

  const send = (t: string, id?: string) =>
    ws?.send(JSON.stringify({ type: t, payload: id ? { id } : {} }));

  const acceptAll = () => {
    send('validate_all_changes');
    applyOpsToUniver(pendingOps);             // apply now
    dispatch({ type: 'CLEAR_PENDING' });
  };

  const rejectAll = () => {
    send('reject_all_changes');
    dispatch({ type: 'CLEAR_PENDING' });
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-window">
        <h3>Mises à jour proposées</h3>
        <ul>
          {pendingOps.map((op) => (
            <li key={op.id}>{op.description}</li>
          ))}
        </ul>
        <button onClick={acceptAll}>Tout accepter</button>{' '}
        <button onClick={rejectAll}>Tout refuser</button>
      </div>
    </div>
  );
}