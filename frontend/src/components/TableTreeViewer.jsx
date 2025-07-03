import React from 'react';
import './TableTreeViewer.css';
import TableRenderer from './TableRenderer';

function renderTable(name, table) {
    return (
        <li key={name}>
            <details>
                <summary>{table.name || name}</summary>
                <TableRenderer table={table} />
            </details>
        </li>
    );
}


export default function TableTreeViewer({ tables = {}, onContinue }) {
    return (
        <div className="table-tree-viewer">
            <h3>ROM Tables</h3>
            <ul className="table-tree">
                {Object.entries(tables).map(([name, tbl]) => renderTable(name, tbl))}
            </ul>
            {onContinue && (
                <button className="btn-continue" onClick={onContinue}>Continue to Analysis</button>
            )}
        </div>
    );
}
