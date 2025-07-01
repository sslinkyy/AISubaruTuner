import React from 'react';
import './AnalysisViewer.css';

function AnalysisViewer({ data }) {
    if (!data) return null;

    // Handle both enhanced and legacy response formats
    const platform = data.platform || 'Unknown';

    // Try to get data from enhanced analysis first, then legacy
    const datalogAnalysis = data.datalog_analysis || {};
    const legacyData = data.legacy_compatibility || {};

    // Map issues from different possible locations
    const issues = datalogAnalysis.issues ||
        legacyData.issues ||
        data.issues ||
        [];

    // Map safety report from different locations
    const safety_report = datalogAnalysis.safety_status ||
        legacyData.safety_report ||
        data.safety_report ||
        {};

    // Create datalog summary from available data
    const summary = datalogAnalysis.summary || {};
    const datalog_summary = {
        total_rows: summary.total_rows || summary.total_records || datalogAnalysis.total_records || data.total_rows || 0,
        total_columns: summary.total_columns || datalogAnalysis.parameters_analyzed || data.total_columns || 0,
        duration: summary.duration || datalogAnalysis.duration_seconds || data.duration || 0,
        issues_found: datalogAnalysis.issues_found || summary.issues_found || issues.length || 0
    };

    const renderIssues = () => {
        if (!issues || issues.length === 0) {
            return (
                <div className="no-issues">
                    <h4>✅ No Critical Issues Found</h4>
                    <p>Your datalog looks clean! No major issues detected.</p>
                </div>
            );
        }

        return (
            <div className="issues-list">
                <h4>⚠️ Issues Detected ({issues.length})</h4>
                {issues.map((issue, index) => (
                    <div key={index} className={`issue-item ${issue.severity || 'medium'}`}>
                        <div className="issue-header">
                            <span className="issue-type">{issue.type || issue.category || 'General'}</span>
                            <span className={`severity-badge ${issue.severity || 'medium'}`}>
                                {(issue.severity || 'MEDIUM').toUpperCase()}
                            </span>
                        </div>
                        <p className="issue-message">{issue.message || issue.description || 'No description'}</p>
                        {(issue.recommendation || issue.solution) && (
                            <p className="issue-recommendation">
                                <strong>Recommendation:</strong> {issue.recommendation || issue.solution}
                            </p>
                        )}
                        {issue.affected_parameters && (
                            <p className="affected-params">
                                <strong>Affected:</strong> {issue.affected_parameters.join(', ')}
                            </p>
                        )}
                    </div>
                ))}
            </div>
        );
    };

    const renderSafetyStatus = () => {
        // Handle different safety report formats
        const safetyStatus = safety_report.overall_status ||
            safety_report.status ||
            (issues.some(i => (i.severity || '').toLowerCase() === 'critical') ? 'warning' : 'safe');

        const criticalIssues = safety_report.critical_issues ||
            issues.filter(i => (i.severity || '').toLowerCase() === 'critical') ||
            [];

        const warnings = safety_report.warnings ||
            issues.filter(i => (i.severity || '').toLowerCase() === 'high') ||
            [];

        const statusColor = safetyStatus === 'safe' ? 'success' : 'danger';

        return (
            <div className={`safety-status ${statusColor}`}>
                <h4>
                    {safetyStatus === 'safe' ? '🛡️' : '⚠️'}
                    Safety Status: {safetyStatus.toUpperCase()}
                </h4>

                {criticalIssues.length > 0 && (
                    <div className="critical-issues">
                        <h5>Critical Safety Issues:</h5>
                        {criticalIssues.map((issue, index) => (
                            <div key={index} className="critical-issue">
                                {issue.message || issue.description || issue}
                            </div>
                        ))}
                    </div>
                )}

                {warnings.length > 0 && (
                    <div className="safety-warnings">
                        <h5>Safety Warnings:</h5>
                        {warnings.map((warning, index) => (
                            <div key={index} className="safety-warning">
                                {warning.message || warning.description || warning}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    const renderEnhancedMetrics = () => {
        if (!data.quality_metrics) return null;

        const metrics = data.quality_metrics;
        return (
            <div className="analysis-section">
                <h3>📊 Analysis Quality</h3>
                <div className="metrics-grid">
                    <div className="metric-item">
                        <span className="metric-label">Analysis Confidence</span>
                        <span className="metric-value">{(metrics.analysis_confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">ROM Compatibility</span>
                        <span className="metric-value">{(metrics.rom_compatibility * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">Data Quality</span>
                        <span className="metric-value">{(metrics.data_quality * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="analysis-viewer">
            <div className="analysis-header">
                <h2>📊 Datalog Analysis Results</h2>
                <div className="platform-info">
                    <span className="platform-badge">{platform}</span>
                    <span className="data-info">
                        {datalog_summary.total_rows} data points • {datalog_summary.total_columns} parameters
                    </span>
                    {data.analysis_type && (
                        <span className="analysis-type-badge">{data.analysis_type}</span>
                    )}
                </div>
            </div>

            <div className="analysis-grid">
                <div className="analysis-section">
                    <h3>🔍 Issue Detection</h3>
                    {renderIssues()}
                </div>

                <div className="analysis-section">
                    <h3>🛡️ Safety Analysis</h3>
                    {renderSafetyStatus()}
                </div>

                {renderEnhancedMetrics()}

                <div className="analysis-section full-width">
                    <h3>📈 Data Summary</h3>
                    <div className="summary-stats">
                        <div className="stat-item">
                            <span className="stat-label">Duration</span>
                            <span className="stat-value">
                                {datalog_summary.duration ?
                                    `${datalog_summary.duration.toFixed(1)}s` :
                                    'Unknown'
                                }
                            </span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Data Points</span>
                            <span className="stat-value">{datalog_summary.total_rows}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Parameters</span>
                            <span className="stat-value">{datalog_summary.total_columns}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Issues Found</span>
                            <span className="stat-value">{datalog_summary.issues_found}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Platform</span>
                            <span className="stat-value">{platform}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Debug info for development */}
            {process.env.NODE_ENV === 'development' && (
                <div className="debug-section">
                    <details>
                        <summary>🔧 Debug: Raw Analysis Data</summary>
                        <pre>{JSON.stringify(data, null, 2)}</pre>
                    </details>
                </div>
            )}
        </div>
    );
}

export default AnalysisViewer;