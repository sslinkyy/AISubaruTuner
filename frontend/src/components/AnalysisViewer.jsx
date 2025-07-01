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
    const datalogObj = datalogAnalysis.datalog || {};
    const datalogRecords = Array.isArray(datalogObj.data) ? datalogObj.data : [];
    const datalog_summary = {
        // Number of rows/records in the datalog
        total_rows: summary.total_rows ||
            summary.total_records ||
            datalogAnalysis.total_rows ||
            datalogAnalysis.total_records ||
            datalogObj.total_rows ||
            datalogRecords.length ||
            data.total_rows ||
            0,
        // Number of parameters/columns logged
        total_columns: summary.total_columns ||
            datalogAnalysis.parameters_analyzed ||
            datalogObj.total_columns ||
            (Array.isArray(summary.columns) ? summary.columns.length : 0) ||
            (Array.isArray(datalogObj.columns) ? datalogObj.columns.length : 0) ||
            data.total_columns ||
            0,
        // Duration of the log in seconds
        duration: summary.duration ||
            datalogAnalysis.duration_seconds ||
            data.duration ||
            0,
        // How many issues were detected
        issues_found: datalogAnalysis.issues_found ||
            summary.issues_found ||
            issues.length ||
            0,
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
                <h4>Issues Detected ({issues.length})</h4>
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
                    {safetyStatus === 'safe' ? 'safe' : 'warning'} Safety Status: {safetyStatus.toUpperCase()}
                </h4>

                {criticalIssues.length > 0 && (
                    <div className="critical-issues">
                        <h5>Critical Safety Issues:</h5>
                        {criticalIssues.map((issue, index) => (
                            <div key={index} className="critical-issue">
                                <div className="issue-header">
                                    <span className="issue-type">{issue.type || 'Issue'}</span>
                                    <span className="severity-badge critical">CRITICAL</span>
                                </div>
                                <p className="issue-message">{issue.message || issue.description || issue}</p>
                                {issue.rpm_range && (
                                    <p className="issue-detail"><strong>RPM:</strong> {issue.rpm_range[0]}-{issue.rpm_range[1]}</p>
                                )}
                                {issue.avg_afr && (
                                    <p className="issue-detail"><strong>Avg AFR:</strong> {issue.avg_afr}</p>
                                )}
                                {issue.max_timing && (
                                    <p className="issue-detail"><strong>Max Timing:</strong> {issue.max_timing}&deg;</p>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {warnings.length > 0 && (
                    <div className="safety-warnings">
                        <h5>Safety Warnings:</h5>
                        {warnings.map((warning, index) => (
                            <div key={index} className="safety-warning">
                                <div className="issue-header">
                                    <span className="issue-type">{warning.type || 'Warning'}</span>
                                    <span className="severity-badge warning">WARNING</span>
                                </div>
                                <p className="issue-message">{warning.message || warning.description || warning}</p>
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

        const formatMetricValue = (value) => {
            if (value === undefined || value === null) return 'N/A';
            if (typeof value === 'number') return `${(value * 100).toFixed(1)}%`;
            if (typeof value === 'object' && value.status) return value.status;
            return String(value);
        };

        return (
            <div className="analysis-section">
                <h3>Analysis Quality</h3>
                <div className="metrics-grid">
                    <div className="metric-item">
                        <span className="metric-label">Analysis Confidence</span>
                        <span className="metric-value">{formatMetricValue(metrics.analysis_confidence)}</span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">ROM Compatibility</span>
                        <span className="metric-value">{formatMetricValue(metrics.rom_compatibility)}</span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">Data Completeness</span>
                        <span className="metric-value">{formatMetricValue(metrics.data_quality || metrics.data_completeness)}</span>
                    </div>
                    {metrics.recommendation_reliability && (
                        <div className="metric-item">
                            <span className="metric-label">Recommendation Reliability</span>
                            <span className="metric-value">{formatMetricValue(metrics.recommendation_reliability)}</span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="analysis-viewer">
            <div className="analysis-header">
                <h2>Datalog Analysis Results</h2>
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
                    <h3>Issue Detection</h3>
                    {renderIssues()}
                </div>

                <div className="analysis-section">
                    <h3>Safety Analysis</h3>
                    {renderSafetyStatus()}
                </div>

                {renderEnhancedMetrics()}

                <div className="analysis-section full-width">
                    <h3>Data Summary</h3>
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

            <div className="debug-section">
                <details>
                    <summary>Analysis Data</summary>
                    <pre>{JSON.stringify(data, null, 2)}</pre>
                </details>
            </div>
        </div>
    );
}

export default AnalysisViewer;
