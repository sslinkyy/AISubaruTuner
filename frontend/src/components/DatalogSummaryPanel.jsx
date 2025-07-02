import React from 'react';
import './DatalogSummaryPanel.css';

function safe(val, fallback = 'N/A') {
    return val !== undefined && val !== null ? val : fallback;
}

export default function DatalogSummaryPanel({ summary = {}, quality = {}, scenarios = {} }) {
    const scenarioKeys = ['wot', 'idle', 'cruise'];
    return (
        <section className="datalog-summary-panel" aria-labelledby="datalog-summary-heading">
            <h3 id="datalog-summary-heading">Datalog Summary</h3>
            <div className="summary-grid">
                <div className="summary-item">
                    <span className="summary-label">Duration</span>
                    <span className="summary-value">{safe(summary.duration)}</span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Samples</span>
                    <span className="summary-value">{safe(summary.sample_count)}</span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Parameters</span>
                    <span className="summary-value">{safe(summary.parameter_count)}</span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Gaps</span>
                    <span className="summary-value">{safe(summary.time_gaps)}</span>
                </div>
            </div>

            {quality && Object.keys(quality).length > 0 && (
                <div className="quality-grid" aria-label="Datalog quality metrics">
                    {Object.entries(quality).map(([k,v]) => (
                        <div key={k} className="quality-item">
                            <span className="quality-label">{k}</span>
                            <span className="quality-value">{safe(v)}</span>
                        </div>
                    ))}
                </div>
            )}

            {scenarios && (
                <div className="scenario-checks">
                    <h4>Required Scenarios</h4>
                    <ul>
                        {scenarioKeys.map(key => (
                            <li key={key} className={scenarios[key] ? 'ok' : 'missing'}>
                                {key.toUpperCase()} {scenarios[key] ? '✔' : '✖'}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
}
