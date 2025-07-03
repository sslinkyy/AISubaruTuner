import React from 'react';
import './TuneTableComparison.css';

// Basic table renderer used for raw ROM tables
function parseLegacyTable(str) {
  if (typeof str !== 'string') return null;
  const lines = str.trim().split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return null;
  const header = lines[0];
  if (header === '[Table3D]' && lines.length >= 2) {
    const yAxis = lines[1].split(/\s+/).map(parseFloat);
    const xAxis = [];
    const data = [];
    for (let i = 2; i < lines.length; i += 1) {
      const parts = lines[i].split(/\s+/).map(parseFloat);
      if (parts.length === yAxis.length + 1) {
        xAxis.push(parts[0]);
        data.push(parts.slice(1));
      }
    }
    return { axes: { x: xAxis, y: yAxis }, data };
  }
  if (header === '[Table2D]' && lines.length >= 3) {
    const xAxis = lines[1].split(/\s+/).map(parseFloat);
    const dataRow = lines[2].split(/\s+/).map(parseFloat);
    return { axes: { x: xAxis }, data: [dataRow] };
  }
  return null;
}

export default function TableRenderer({ table }) {
  if (!table) return null;
  let { data, axes = {}, rpm_axis, load_axis } = table;
  if (typeof data === 'string') {
    const parsed = parseLegacyTable(data);
    if (parsed) {
      axes = { ...axes, ...parsed.axes };
      data = parsed.data;
    } else {
      return null;
    }
  }
  const xAxis = axes.x || rpm_axis || [];
  const yAxis = axes.y || load_axis || [];
  const zAxis = axes.z || [];

  if (!data || data.length === 0) return null;

  const is3D = Array.isArray(data) && Array.isArray(data[0]) && Array.isArray(data[0][0]);
  const is1D = Array.isArray(data) && (!Array.isArray(data[0]) || (!is3D && (yAxis.length === 0 || data.length === 1)));

  if (is3D) {
    return (
      <div className="table-3d">
        {data.map((plane, idx) => (
          <div key={idx} className="table-plane">
            <div className="plane-label">{zAxis[idx] ?? `Layer ${idx}`}</div>
            <TableRenderer table={{ axes: { x: xAxis, y: yAxis }, data: plane }} />
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
          {data[0].map((val, cIdx) => (
            <tr key={cIdx}>
              <th>{xAxis[cIdx] ?? cIdx}</th>
              <td>{val}</td>
            </tr>
          ))}
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
        {data.map((row, rIdx) => (
          <tr key={rIdx}>
            <th>{xAxis[rIdx] ?? rIdx}</th>
            {row.map((val, cIdx) => (
              <td key={cIdx}>{val}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
