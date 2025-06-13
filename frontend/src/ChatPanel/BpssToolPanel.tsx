import React, { useState, useRef } from 'react';
import './BpssToolPanel.css';

interface FileSlotProps {
    label: string;
    file: File | null;
    onFileChange: (file: File) => void;
    onFileClear: () => void;
}

const FileSlot: React.FC<FileSlotProps> = ({ label, file, onFileChange, onFileClear }) => {
    const inputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files?.[0]) {
            onFileChange(event.target.files[0]);
        }
    };

    return (
        <div className="file-slot">
            <input
                type="file"
                ref={inputRef}
                onChange={handleFileSelect}
                accept=".xlsx"
                style={{ display: 'none' }}
            />
            <label className="file-slot-label">{label}</label>
            {file ? (
                <div className="file-info">
                    <span className="file-name" title={file.name}>
                        ✅ {file.name}
                    </span>
                    <button onClick={onFileClear} className="clear-button">
                        ✕
                    </button>
                </div>
            ) : (
                <button onClick={() => inputRef.current?.click()} className="attach-button">
                    Attach File
                </button>
            )}
        </div>
    );
};


interface BpssToolPanelProps {
    onProcess: (formData: FormData) => void;
    isProcessing: boolean;
}

const BpssToolPanel: React.FC<BpssToolPanelProps> = ({ onProcess, isProcessing }) => {
    const [files, setFiles] = useState<{ [key: string]: File | null }>({
        ppes: null,
        dpp18: null,
        bud45: null,
    });
    const [year, setYear] = useState(new Date().getFullYear() + 1);
    const [ministry, setMinistry] = useState('38');
    const [program, setProgram] = useState('150');

    const handleFileChange = (key: string, file: File) => {
        setFiles(prev => ({ ...prev, [key]: file }));
    };

    const handleFileClear = (key: string) => {
        setFiles(prev => ({ ...prev, [key]: null }));
    };

    const handleSubmit = () => {
        if (!files.ppes || !files.dpp18 || !files.bud45) {
            alert("Please upload all three required files.");
            return;
        }

        const formData = new FormData();
        formData.append('ppes', files.ppes);
        formData.append('dpp18', files.dpp18);
        formData.append('bud45', files.bud45);
        formData.append('year', String(year));
        formData.append('ministry', ministry);
        formData.append('program', program);

        onProcess(formData);
    };

    const allFilesReady = !!(files.ppes && files.dpp18 && files.bud45);

    return (
        <div className="bpss-tool-panel">
            <h3 className="bpss-tool-header">🛠️ Outil BPSS</h3>
            <p className="bpss-tool-caption">
                Traitez automatiquement vos fichiers budgétaires.
            </p>

            <div className="bpss-inputs-grid">
                 <FileSlot label="PP-E-S" file={files.ppes} onFileChange={(f) => handleFileChange('ppes', f)} onFileClear={() => handleFileClear('ppes')} />
                 <FileSlot label="DPP18" file={files.dpp18} onFileChange={(f) => handleFileChange('dpp18', f)} onFileClear={() => handleFileClear('dpp18')} />
                 <FileSlot label="BUD45" file={files.bud45} onFileChange={(f) => handleFileChange('bud45', f)} onFileClear={() => handleFileClear('bud45')} />
            </div>

            <div className="bpss-params-grid">
                <div className="param-input">
                    <label>Année</label>
                    <input type="number" value={year} onChange={e => setYear(Number(e.target.value))} />
                </div>
                 <div className="param-input">
                    <label>Ministère</label>
                    <input type="text" value={ministry} onChange={e => setMinistry(e.target.value)} />
                </div>
                 <div className="param-input">
                    <label>Programme</label>
                    <input type="text" value={program} onChange={e => setProgram(e.target.value)} />
                </div>
            </div>

            <button
                className="process-button"
                onClick={handleSubmit}
                disabled={!allFilesReady || isProcessing}
            >
                {isProcessing ? 'Processing...' : 'Lancer le traitement'}
            </button>
        </div>
    );
};

export default BpssToolPanel;