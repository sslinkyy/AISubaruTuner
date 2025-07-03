import React from 'react';
import './TableTreeViewer.css';

function renderNode(name, value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        return (
            <li key={name}>
                <details>
                    <summary>{name}</summary>
                    <ul>
                        {Object.entries(value).map(([k, v]) => renderNode(k, v))}
                    </ul>
                </details>
            </li>
        );
    }
    return (
        <li key={name}>
            <span className="leaf-name">{name}:</span> {String(value)}
        </li>
    );
}

export default function TableTreeViewer({ tables = {}, onContinue }) {
    return (
        <div className="table-tree-viewer">
            <h3>ROM Tables</h3>
            <ul className="table-tree">
                {Object.entries(tables).map(([name, tbl]) => renderNode(name, tbl))}
            </ul>
            {onContinue && (
                <button className="btn-continue" onClick={onContinue}>Continue to Analysis</button>
            )}
        </div>
    );
}
