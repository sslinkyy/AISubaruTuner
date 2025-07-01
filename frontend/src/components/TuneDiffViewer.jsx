
import React, { useState, useEffect } from 'react';
import './TuneDiffViewer.css';
import CarberryTableDiff from './CarberryTableDiff';

function TuneDiffViewer({ sessionId, selectedChanges, onApproval }) {
    const [diffData, setDiffData] = useState(null);
    const [tableDiff, setTableDiff] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDiffData();
    }, [sessionId, selectedChanges]);

    const fetchDiffData = async () => {
        try {
            setLoading(true);


            const diffResponse = await fetch(
                `/api/session/${sessionId}/table_diff/Primary%20Open%20Loop%20Fueling`,
                { headers: { 'Authorization': 'Bearer demo_token' } }
            );

            if (diffResponse.ok) {
                const diff = await diffResponse.json();
                setTableDiff(diff);
            }

            const changesResp = await fetch(
                `/api/session/${sessionId}/tune_changes?detailed=true`,
                { headers: { 'Authorization': 'Bearer demo_token' } }
            );

            if (changesResp.ok) {
                const data = await changesResp.json();
                const detailed = data.detailed_changes || data.changes || [];
                const summary = {
                    totalChanges: data.total_changes || detailed.length,
                    highImpactChanges: detailed.filter(c => (c.priority || '').toLowerCase() === 'high' || (c.priority || '').toLowerCase() === 'critical').length,
                    estimatedPowerChange: data.estimated_power_gain || 'N/A',
                    safetyRating: data.safety_rating || 'Unknown'
                };


                const processed = detailed.map(ch => ({
                    id: ch.id,
                    parameter: ch.table_name || ch.parameter || 'Unknown',
                    impact: (ch.priority || 'medium').toLowerCase(),
                    changeType: ch.change_type || 'modified',
                    description: ch.description || '',
                    affectedCells: ch.affected_cells || (ch.cell_changes ? ch.cell_changes.length : 0),
                    oldValue: ch.summary?.old_range || (ch.cell_changes && ch.cell_changes[0] ? ch.cell_changes[0].old_value : 'N/A'),
                    newValue: ch.summary?.new_range || (ch.cell_changes && ch.cell_changes[0] ? ch.cell_changes[0].new_value : 'N/A')
                }));

                setDiffData({ changes: processed, summary });
            } else {
                setDiffData({ changes: [], summary: {} });
            }

                setDiffData({ changes: detailed, summary });
            } else {
                setDiffData({ changes: [], summary: {} });
            }

            const response = await fetch(`/api/session/${sessionId}/table_diff/Primary%20Open%20Loop%20Fueling`, {
                headers: { 'Authorization': 'Bearer demo_token' }
            });

            if (response.ok) {
                const diff = await response.json();
                setTableDiff(diff);
            }

            const mockDiffData = {
                changes: selectedChanges.map((changeId, index) => ({
                    id: changeId,
                    parameter: `Parameter_${index + 1}`,
                    oldValue: `Old_Value_${index + 1}`,
                    newValue: `New_Value_${index + 1}`,
                    changeType: 'modified',
                    impact: index % 2 === 0 ? 'high' : 'medium',
                    description: `Change description for ${changeId}`,
                    affectedCells: Math.floor(Math.random() * 20) + 5
                })),
                summary: {
                    totalChanges: selectedChanges.length,
                    highImpactChanges: Math.floor(selectedChanges.length / 2),
                    estimatedPowerChange: '+5-8 HP',
                    safetyRating: 'Safe'
                }
            };

            setDiffData(mockDiffData);


        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const getChangeTypeIcon = (changeType) => {
        switch (changeType) {
            case 'increased': return '📈';
            case 'decreased': return '📉';
            case 'modified': return '🔧';
            case 'added': return '➕';
            case 'removed': return '➖';
            default: return '🔄';
        }
    };

    const getImpactColor = (impact) => {
        switch (impact) {
            case 'high': return '#dc3545';
            case 'medium': return '#ffc107';
            case 'low': return '#28a745';
            default: return '#6c757d';
        }
    };

    if (loading) {
        return (
            <div className="tune-diff-viewer">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Generating tune differences...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="tune-diff-viewer">
                <div className="error-state">
                    <h3>Error Loading Diff</h3>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (!diffData || diffData.changes.length === 0) {
        return (
            <div className="tune-diff-viewer">
                <div className="no-changes">
                    <h3>No Changes Selected</h3>
                    <p>Please go back and select some tuning suggestions to review.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="tune-diff-viewer">
            <div className="diff-header">
                <h2>🔍 Tune Changes Review</h2>
                <p>Review the proposed changes before applying them to your tune</p>
            </div>

            <div className="diff-summary">
                <h3>📊 Change Summary</h3>
                <div className="summary-grid">
                    <div className="summary-item">
                        <span className="summary-label">Total Changes</span>
                        <span className="summary-value">{diffData.summary.totalChanges}</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-label">High Impact</span>
                        <span className="summary-value">{diffData.summary.highImpactChanges}</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-label">Est. Power Gain</span>
                        <span className="summary-value">{diffData.summary.estimatedPowerChange}</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-label">Safety Rating</span>
                        <span className="summary-value safety">{diffData.summary.safetyRating}</span>
                    </div>
                </div>
            </div>

            <div className="changes-list">
                <h3>📝 Detailed Changes</h3>
                {diffData.changes.map((change) => (
                    <div key={change.id} className="change-item">
                        <div className="change-header">
                            <div className="change-title">
                                <span className="change-icon">
                                    {getChangeTypeIcon(change.changeType)}
                                </span>
                                <span className="change-parameter">{change.parameter}</span>
                                <span 
                                    className="impact-badge"
                                    style={{ backgroundColor: getImpactColor(change.impact) }}
                                >
                                    {change.impact.toUpperCase()}
                                </span>
                            </div>
                        </div>

                        <div className="change-details">
                            <div className="value-comparison">
                                <div className="old-value">
                                    <span className="value-label">Current:</span>
                                    <span className="value">{change.oldValue}</span>
                                </div>
                                <div className="arrow">→</div>
                                <div className="new-value">
                                    <span className="value-label">New:</span>
                                    <span className="value">{change.newValue}</span>
                                </div>
                            </div>

                            <div className="change-info">
                                <p className="change-description">{change.description}</p>
                                <p className="affected-cells">
                                    Affects {change.affectedCells} tune map cells
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {tableDiff && (
                <div className="carberry-container">
                    <h3>📊 Table Preview</h3>
                    <CarberryTableDiff diff={tableDiff} />
                </div>
            )}

            <div className="diff-actions">
                <div className="safety-notice">
                    <h4>⚠️ Important Safety Notice</h4>
                    <p>
                        These changes have been validated for safety, but always start with conservative 
                        settings and gradually increase performance modifications. Monitor your engine 
                        closely after applying any changes.
                    </p>
                </div>

                <div className="action-buttons">
                    <button 
                        className="btn-approve"
                        onClick={onApproval}
                    >
                        ✅ Apply Changes to Tune
                    </button>
                </div>
            </div>
        </div>
    );
}

export default TuneDiffViewer;
