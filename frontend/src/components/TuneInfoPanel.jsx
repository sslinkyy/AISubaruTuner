import React from 'react';
import './TuneInfoPanel.css';

function TuneInfoPanel({ romAnalysis, metadata, tuneFile }) {
    if (!romAnalysis) return null;

    const formatItem = (label, value, extra = null) => (
        <div className="info-item">
            <span className="info-label">{label}</span>
            <span className="info-value">{value !== undefined && value !== null ? String(value) : 'N/A'}</span>
            {extra}
        </div>
    );

    return (
        <div className="tune-info-panel">
            <h3>Tune & ROM Details</h3>
            <div className="info-grid">
                {tuneFile && tuneFile.filename && formatItem('File Name', tuneFile.filename)}
                {tuneFile && tuneFile.size !== undefined && formatItem('File Size', `${(tuneFile.size/1024).toFixed(1)} KB`)}
                {romAnalysis.format && formatItem('Format', romAnalysis.format)}
                {romAnalysis.rom_size !== undefined && formatItem('ROM Size', `${romAnalysis.rom_size} bytes`)}
                {romAnalysis.checksum && formatItem('Checksum', romAnalysis.checksum)}
                {romAnalysis.ecu_id && formatItem('ECU ID', romAnalysis.ecu_id)}
                {romAnalysis.tables_parsed !== undefined && formatItem('Tables Parsed', romAnalysis.tables_parsed,
                    romAnalysis.tables_parsed < 100 ? <span className="warning">!</span> : null)}
                {romAnalysis.definition_source && formatItem('Definition', romAnalysis.definition_source,
                    romAnalysis.definition_link && <a href={romAnalysis.definition_link} target="_blank" rel="noopener noreferrer">View</a>)}
                {metadata && metadata.parser_version && formatItem('Parser Version', metadata.parser_version)}
            </div>
        </div>
    );
}

export default TuneInfoPanel;
