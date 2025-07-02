import React from 'react';
import './SessionContextPanel.css';

function safe(value, fallback = 'N/A') {
    return value !== undefined && value !== null && value !== '' ? value : fallback;
}

export default function SessionContextPanel({ vehicle = {}, session = {} }) {
    const mods = Array.isArray(vehicle.mods) ? vehicle.mods : [];

    return (
        <section className="session-context-panel" aria-labelledby="session-context-heading">
            <h3 id="session-context-heading">Vehicle & Session Context</h3>
            <div className="info-grid">
                {vehicle.vin && (
                    <div className="info-item">
                        <span className="info-label">VIN</span>
                        <span className="info-value">{vehicle.vin}</span>
                    </div>
                )}
                {(vehicle.year || vehicle.make || vehicle.model) && (
                    <div className="info-item">
                        <span className="info-label">Vehicle</span>
                        <span className="info-value">
                            {[safe(vehicle.year, ''), safe(vehicle.make, ''), safe(vehicle.model, '')].filter(Boolean).join(' ')}
                        </span>
                    </div>
                )}
                {vehicle.owner && (
                    <div className="info-item">
                        <span className="info-label">Owner</span>
                        <span className="info-value">{vehicle.owner}</span>
                    </div>
                )}
                {vehicle.fuel_type && (
                    <div className="info-item">
                        <span className="info-label">Fuel Type</span>
                        <span className="info-value">{vehicle.fuel_type}</span>
                    </div>
                )}
                {vehicle.region && (
                    <div className="info-item">
                        <span className="info-label">Region</span>
                        <span className="info-value">{vehicle.region}</span>
                    </div>
                )}
                {session.date && (
                    <div className="info-item">
                        <span className="info-label">Log Date</span>
                        <span className="info-value">{new Date(session.date).toLocaleString()}</span>
                    </div>
                )}
            </div>

            {mods.length > 0 && (
                <div className="mods-list">
                    <h4>Modifications</h4>
                    <ul>
                        {mods.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                </div>
            )}

            {vehicle.notes && (
                <div className="vehicle-notes">
                    <h4>Notes</h4>
                    <p>{vehicle.notes}</p>
                </div>
            )}
        </section>
    );
}
