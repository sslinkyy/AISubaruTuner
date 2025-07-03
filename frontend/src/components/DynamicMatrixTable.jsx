import React from 'react';
import './DynamicMatrixTable.css';

// note: renders a matrix table based solely on provided axis definitions
export default function DynamicMatrixTable({
  xAxis,
  yAxis,
  cells,
  className = '',
  onDownload,
}) {
  if (!xAxis || !yAxis || !Array.isArray(cells)) return null;

  // note: build CSV representation for download callback
  const buildCsv = () => {
    const header = [''].concat(xAxis.values).join(',');
    const rows = yAxis.values.map((y, idx) => {
      const row = [y].concat(cells[idx]);
      return row.join(',');
    });
    return [header, ...rows].join('\n');
  };

  const handleDownload = () => {
    if (onDownload) {
      onDownload(buildCsv());
    }
  };

  const shouldHighlight = (rIdx, cIdx) => {
    const val = Number(cells[rIdx][cIdx]);
    if (Number.isNaN(val)) return false;

    let neighbor;
    if (cIdx > 0) {
      neighbor = Number(cells[rIdx][cIdx - 1]);
    } else if (rIdx > 0) {
      neighbor = Number(cells[rIdx - 1][cIdx]);
    }
    if (neighbor === undefined || Number.isNaN(neighbor) || neighbor === 0) return false;
    return Math.abs(val - neighbor) / Math.abs(neighbor) > 0.1;
  };

  return (
    <div className={`dynamic-matrix-table ${className}`}>
      {onDownload && (
        <div className="matrix-actions">
          <button
            className="download-btn"
            aria-label="Download table as CSV"
            onClick={handleDownload}
          >
            \uD83D\uDCE5
          </button>
        </div>
      )}
      <div className="matrix-scroll">
        <table aria-label="Matrix data table">
          <thead>
            <tr>
              <th></th>
              {xAxis.values.map((val, i) => (
                <th key={i} scope="col" title={xAxis.label}>
                  {val} {xAxis.units}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yAxis.values.map((yVal, rIdx) => (
              <tr key={rIdx}>
                <th scope="row" title={yAxis.label}>
                  {yVal} {yAxis.units}
                </th>
                {xAxis.values.map((x, cIdx) => (
                  <td
                    key={cIdx}
                    className={shouldHighlight(rIdx, cIdx) ? 'highlight-cell' : ''}
                  >
                    {cells[rIdx][cIdx]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
