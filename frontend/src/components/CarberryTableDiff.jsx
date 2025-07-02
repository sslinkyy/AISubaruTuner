import React from 'react';
import './CarberryTableDiff.css';

export default function CarberryTableDiff({ diff }) {
  if (!diff || !diff.rpm_axis) return null;

  const { rpm_axis, load_axis, current, proposed, difference, units } = diff;

  const formatValue = (val) => {
    if (typeof val === 'number') {
      return val.toFixed(2);
    }
    return val;
  };

  return (
    <div className="carberry-diff">
      <table className="carberry-table">
        <thead>
          <tr>
            <th>RPM \ Load</th>
            {load_axis.map((l, i) => (
              <th key={i}>{formatValue(l)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rpm_axis.map((rpm, rIdx) => (
            <tr key={rIdx}>
              <th>{formatValue(rpm)}</th>
              {proposed[rIdx].map((val, cIdx) => {
                const delta = difference[rIdx][cIdx];
                const className = delta > 0 ? 'increase' : delta < 0 ? 'decrease' : '';
                const oldVal = formatValue(current[rIdx][cIdx]);
                return (
                  <td key={cIdx} className={className} title={`Old: ${oldVal}`}> 
                    {formatValue(val)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {units && <div className="units">Units: {units}</div>}
    </div>
  );
}
