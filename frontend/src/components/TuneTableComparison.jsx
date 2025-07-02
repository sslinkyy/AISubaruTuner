import React from 'react';
import './TuneTableComparison.css';

// Download helper for exporting table data as CSV
function downloadCsv(data, name) {
  if (!data) return;
  const csv = data.map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

function renderTable(table, compare = null) {
  const { axes = {}, data } = table;
  const xAxis = axes.x || [];
  const yAxis = axes.y || [];

  if (!data || data.length === 0) return null;

  return (
    <table className="tune-table" role="table">
      <thead>
        <tr>
          <th>{'RPM \\ Load'}</th>
          {yAxis.map((v, i) => (
            <th key={i}>{v}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {xAxis.map((x, rIdx) => (
          <tr key={rIdx}>
            <th>{x}</th>
            {data[rIdx].map((val, cIdx) => {
              const changed = compare && compare[rIdx] && compare[rIdx][cIdx] !== val;
              return (
                <td key={cIdx} className={changed ? 'changed-cell' : ''}>{val}</td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function TuneTableComparison({ tables = [], onContinue }) {
  if (!tables.length) return null;

  return (
    <div className="table-comparison">
      {tables.map((tbl) => (
        <div key={tbl.id} className="table-section">
          <h3>{tbl.name}</h3>
          <div className="tables-wrapper">
            <div className="single-table">
              <div className="table-header">
                <span>Original</span>
                <button onClick={() => downloadCsv(tbl.original, `${tbl.id}_original`)}>Download</button>
              </div>
              {renderTable({ axes: tbl.axes, data: tbl.original })}
            </div>
            <div className="single-table">
              <div className="table-header">
                <span>Suggested</span>
                <button onClick={() => downloadCsv(tbl.modified, `${tbl.id}_modified`)}>Download</button>
              </div>
              {renderTable({ axes: tbl.axes, data: tbl.modified }, tbl.original)}
            </div>
          </div>
        </div>
      ))}
      {onContinue && (
        <div className="comparison-actions">
          <button className="btn-continue" onClick={onContinue}>Continue</button>
        </div>
      )}
    </div>
  );
}
