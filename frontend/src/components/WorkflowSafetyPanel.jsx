import React, { useState } from 'react';
import './WorkflowSafetyPanel.css';

export default function WorkflowSafetyPanel({ history = [], chat = [], checklist = [], riskStatement = '', onAcknowledge }) {
    const [ack, setAck] = useState(false);

    const handleAck = () => {
        setAck(!ack);
        if (!ack && onAcknowledge) onAcknowledge();
    };

    return (
        <section className="workflow-safety-panel" aria-labelledby="workflow-heading">
            <h3 id="workflow-heading">Workflow, Communication &amp; Safety</h3>

            {history.length > 0 && (
                <div className="history-section">
                    <h4>Session History</h4>
                    <ul>{history.map((h, i) => <li key={i}>{h}</li>)}</ul>
                </div>
            )}

            {chat.length > 0 && (
                <div className="chat-section">
                    <h4>Chat Log</h4>
                    <ul>{chat.map((c, i) => <li key={i}>{c}</li>)}</ul>
                </div>
            )}

            {checklist.length > 0 && (
                <div className="checklist-section">
                    <h4>Safety Checklist</h4>
                    <ul>{checklist.map((c, i) => <li key={i}>{c}</li>)}</ul>
                </div>
            )}

            {riskStatement && (
                <div className="risk-statement">
                    <p>{riskStatement}</p>
                    <label>
                        <input type="checkbox" checked={ack} onChange={handleAck} /> I acknowledge the risk
                    </label>
                </div>
            )}
        </section>
    );
}
