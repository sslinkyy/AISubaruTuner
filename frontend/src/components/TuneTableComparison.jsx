import React from 'react';
import './TuneTableComparison.css';

// Download helper for exporting table data as CSV
function downloadCsv(data, name) {
  if (!data) return;

  let rows = [];

  if (Array.isArray(data[0]) && Array.isArray(data[0][0])) {
    // 3D table - flatten planes
    data.forEach((plane, pIdx) => {
      rows.push([`Layer ${pIdx}`]);
      plane.forEach((r) => rows.push(r));
      rows.push([]); // blank line between planes
    });
  } else {
    rows = data;
  }

  const csv = rows.map((row) => row.join(',')).join('\n');
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
  const zAxis = axes.z || [];

  if (!data || data.length === 0) return null;

  // Detect table dimensionality
  const is3D = Array.isArray(data[0]) && Array.isArray(data[0][0]);
  const is1D = !Array.isArray(data[0]) || (!is3D && (yAxis.length === 0 || data.length === 1));

  if (is3D) {
    return (
      <div className="table-3d">
        {data.map((plane, idx) => (
          <div key={idx} className="table-plane">
            <div className="plane-label">{zAxis[idx] ?? `Layer ${idx}`}</div>
            {renderTable({ axes: { x: xAxis, y: yAxis }, data: plane }, compare ? compare[idx] : null)}
          </div>
        ))}
      </div>
    );
  }

  if (is1D) {
    return (
      <table className="tune-table" role="table">
        <thead>
          <tr>
            <th>{xAxis.join(' / ') || 'Index'}</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {data[0].map((val, cIdx) => {
            const changed = compare && compare[0] && compare[0][cIdx] !== val;
            return (
              <tr key={cIdx}>
                <th>{xAxis[cIdx] ?? cIdx}</th>
                <td className={changed ? 'changed-cell' : ''}>{val}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }

  return (
    <table className="tune-table" role="table">
      <thead>
        <tr>
          <th>{xAxis.join(' / ') || 'RPM'} \ {yAxis.join(' / ') || 'Load'}</th>
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
  if (!tables.length) return (
    <div className="table-comparison empty" role="alert">
      No tables to compare. Selected suggestions may not modify any ROM tables.
    </div>
  );

  const priorityColor = (p) => {
    switch ((p || '').toLowerCase()) {
      case 'critical':
        return '#dc3545';
      case 'high':
        return '#fd7e14';
      case 'medium':
        return '#ffc107';
      case 'low':
      default:
        return '#28a745';
    }
  };

  const priorityIcon = (p) => {
    switch ((p || '').toLowerCase()) {
      case 'critical':
        return '🚨';
      case 'high':
        return '⚠️';
      case 'medium':
        return '🔧';
      default:
        return '✅';
    }
  };

  return (
    <div className="table-comparison">
      {tables.map((tbl) => (
        <div key={tbl.id} className="table-section">
          <h3>
            {priorityIcon(tbl.priority)} {tbl.name}
            {tbl.table_type && (
              <span className="type-badge">{tbl.table_type}</span>
            )}
          </h3>
          <div className="tables-wrapper">
            <div className="single-table">
              <div className="table-header">
                <span>Original</span>
                <button
                  className="download-btn"
                  title="Download original"
                  onClick={() => downloadCsv(tbl.original, `${tbl.id}_original`)}
                >
                  📥
                </button>
              </div>
              {renderTable({ axes: tbl.axes, data: tbl.original })}
            </div>
            <div className="single-table">
              <div className="table-header">
                <span style={{ color: priorityColor(tbl.priority) }}>Suggested</span>
                <button
                  className="download-btn"
                  title="Download modified"
                  onClick={() => downloadCsv(tbl.modified, `${tbl.id}_modified`)}
                >
                  📥
                </button>
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
