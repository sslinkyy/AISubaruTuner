import React from 'react';
import './AnalysisReport.css';

function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function AnalysisReport({ metadata, romCompatibility }) {
    if (!metadata) return null;

    return (
        <div className="analysis-report">
            <h3>Analysis Report</h3>
            <div className="metadata-grid">
                {Object.entries(metadata).map(([key, value]) => (
                    <div key={key} className="metadata-item">
                        <span className="meta-label">{formatLabel(key)}</span>
                        <span className="meta-value">{String(value)}</span>
                    </div>
                ))}
            </div>
            {romCompatibility && (
                <div className="rom-compatibility">
                    <h4>ROM Compatibility</h4>
                    <pre>{JSON.stringify(romCompatibility, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}

export default AnalysisReport;
