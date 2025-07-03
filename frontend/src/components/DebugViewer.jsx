import React from 'react';
import './AnalysisViewer.css';

export default function DebugViewer({ data, onBack }) {
    return (
        <div className="debug-viewer">
            <h3>Debug Information</h3>
            <pre style={{ maxHeight: '60vh', overflow: 'auto' }}>
                {JSON.stringify(data, null, 2)}
            </pre>
            {onBack && (
                <button className="btn btn-primary" onClick={onBack}>Back</button>
            )}
        </div>
    );
}
