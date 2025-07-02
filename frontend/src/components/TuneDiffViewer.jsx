import React, { useState, useEffect, useCallback } from 'react';
import './TuneDiffViewer.css';
import CarberryTableDiff from './CarberryTableDiff';
import AnalysisReport from './AnalysisReport';
import TuneInfoPanel from './TuneInfoPanel';
import LoadingSpinner from './LoadingSpinner';
import WorkflowSafetyPanel from './WorkflowSafetyPanel';

function TuneDiffViewer({ sessionId, analysisData, selectedChanges, onApproval }) {
    const [diffData, setDiffData] = useState(null);
    const [tableDiff, setTableDiff] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchDiffData = useCallback(async () => {
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
                    highImpactChanges: detailed.filter(
                        (c) => (c.priority || '').toLowerCase() === 'high' || (c.priority || '').toLowerCase() === 'critical'
                    ).length,
                    estimatedPowerChange: data.estimated_power_gain || 'N/A',
                    safetyRating: data.safety_rating || 'Unknown'
                };

                setDiffData({
                    changes: detailed,
                    summary,
                    analysisMetadata: data.analysis_metadata,
                    romCompatibility: data.rom_compatibility,
                    fileInfo: data.file_info
                });
            } else {
                setDiffData({ changes: [], summary: {} });
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [sessionId, selectedChanges]);

    useEffect(() => {
        fetchDiffData();
    }, [fetchDiffData]);

    const getChangeTypeIcon = (changeType) => {
        switch (changeType) {
            case 'increased':
                return '⬆️';
            case 'decreased':
                return '⬇️';
            case 'added':
                return '➕';
            case 'removed':
                return '➖';
            case 'modified':
                return '✏️';
            default:
                return '';
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
                <LoadingSpinner message="Generating tune differences..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="tune-diff-viewer">
                <div className="error-state" role="alert">
                    <h3>Error Loading Diff</h3>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (!diffData || diffData.changes.length === 0) {
        return (
            <div className="tune-diff-viewer">
                <div className="no-changes" role="alert">
                    <h3>No Changes Selected</h3>
                    <p>Please go back and select some tuning suggestions to review.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="tune-diff-viewer">
            <TuneInfoPanel
                romAnalysis={analysisData?.rom_analysis || diffData.analysisMetadata?.rom_analysis}
                metadata={diffData.analysisMetadata}
                tuneFile={analysisData?.file_info?.tune || diffData.fileInfo?.tune}
            />
            <div className="diff-header">
                <h2>Tune Changes Review</h2>
                <p>Review the proposed changes before applying them to your tune</p>
            </div>

            <div className="diff-summary">
                <h3>Change Summary</h3>
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
                <h3>Detailed Changes</h3>
                {diffData.changes.map((change) => (
                    <div key={change.id} className="change-item">
                        <div className="change-header">
                            <div className="change-title">
                                <span className="change-icon" aria-hidden="true">
                                    {getChangeTypeIcon(change.changeType)}
                                </span>
                                <span className="change-parameter">{change.parameter}</span>
                                <span
                                    className="impact-badge"
                                    style={{ backgroundColor: getImpactColor(change?.impact || change?.priority) }}
                                    aria-label={`${change?.impact || change?.priority} impact`}
                                >
                                    {(change?.impact || change?.priority || 'medium').toUpperCase()}
                                </span>
                            </div>
                        </div>

                        <div className="change-details">
                            <div className="value-comparison">
                                <div className="old-value">
                                    <span className="value-label">Current:</span>
                                    <span className="value">{change.summary?.old_range || 'N/A'}</span>
                                </div>
                                <div className="arrow">→</div>
                                <div className="new-value">
                                    <span className="value-label">New:</span>
                                    <span className="value">{change.summary?.new_range || 'N/A'}</span>
                                </div>
                            </div>

                            <div className="change-info">
                                <p className="change-description">{change.description}</p>
                                <p className="affected-cells">
                                    Affects {change.affected_cells} tune map cells
                                </p>
                                {change.summary && (
                                    <p className="change-stats">
                                        Avg {change.summary.avg_change}, Max {change.summary.max_change}
                                    </p>
                                )}
                                {change.predicted_effect && (
                                    <p className="change-stats">
                                        {change.predicted_effect.performance && (
                                            <span>Perf: {change.predicted_effect.performance}; </span>
                                        )}
                                        {change.predicted_effect.safety && (
                                            <span>Safety: {change.predicted_effect.safety}; </span>
                                        )}
                                        {change.predicted_effect.forecast && (
                                            <span>Forecast: {change.predicted_effect.forecast}; </span>
                                        )}
                                        {change.confidence && (
                                            <span>Confidence: {change.confidence}</span>
                                        )}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {tableDiff && (
                <div className="carberry-container">
                    <h3>Table Preview</h3>
                    <CarberryTableDiff diff={tableDiff} />
                </div>
            )}

            {diffData.analysisMetadata && (
                <AnalysisReport
                    metadata={diffData.analysisMetadata}
                    romCompatibility={diffData.romCompatibility}
                />
            )}

            <WorkflowSafetyPanel
                history={diffData.history || []}
                chat={diffData.chat || []}
                checklist={diffData.checklist || []}
                riskStatement={diffData.risk_statement}
            />

            <div className="diff-actions">
                <div className="safety-notice">
                    <h4>Important Safety Notice</h4>
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
                        Apply Changes to Tune
                    </button>
                </div>
            </div>
        </div>
    );
}

export default TuneDiffViewer;
