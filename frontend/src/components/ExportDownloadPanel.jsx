
import React, { useState } from 'react';
import './ExportDownloadPanel.css';

function ExportDownloadPanel({ sessionId, onDownloadComplete }) {
    const [downloading, setDownloading] = useState(false);
    const [downloadComplete, setDownloadComplete] = useState(false);
    const [error, setError] = useState(null);

    const handleDownload = async () => {
        setDownloading(true);
        setError(null);

        try {
            const response = await fetch(`/api/download/${sessionId}`, {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer demo_token'
                }
            });

            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `optimized_tune_${sessionId}_${new Date().toISOString().slice(0, 10)}.bin`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            setDownloadComplete(true);
            setTimeout(() => {
                onDownloadComplete();
            }, 2000);

        } catch (err) {
            setError(err.message);
        } finally {
            setDownloading(false);
        }
    };

    const handleGenerateReport = async () => {
        try {
            // Generate a tuning report
            const reportData = {
                sessionId,
                timestamp: new Date().toISOString(),
                changes: 'Applied optimizations based on datalog analysis',
                recommendations: 'Monitor engine parameters after installation'
            };

            const blob = new Blob([JSON.stringify(reportData, null, 2)], { 
                type: 'application/json' 
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tuning_report_${sessionId}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (err) {
            setError('Failed to generate report: ' + err.message);
        }
    };

    return (
        <div className="export-download-panel">
            <div className="download-header">
                <h2>Tune Optimization Complete!</h2>
                <p>Your optimized tune is ready for download</p>
            </div>

            <div className="download-content">
                {!downloadComplete ? (
                    <>
                        <div className="download-info">
                            <div className="info-card">
                                <h3>Your Optimized Tune</h3>
                                <ul>
                                    <li>Safety validated</li>
                                    <li>Performance optimized</li>
                                    <li>Ready for installation</li>
                                    <li>Backup recommended</li>
                                </ul>
                            </div>

                            <div className="info-card">
                                <h3>Installation Guidelines</h3>
                                <ul>
                                    <li>Use proper flashing tools</li>
                                    <li>Ensure stable power supply</li>
                                    <li>Keep original tune backup</li>
                                    <li>Monitor initial drives carefully</li>
                                </ul>
                            </div>
                        </div>

                        {error && (
                            <div className="error-message">
                                ❌ {error}
                            </div>
                        )}

                        <div className="download-actions">
                            <button 
                                className="btn-download primary"
                                onClick={handleDownload}
                                disabled={downloading}
                            >
                                {downloading ? (
                                    <>
                                        <span className="spinner-small"></span>
                                        Preparing Download...
                                    </>
                                ) : (
                                    <>
                                        Download Optimized Tune
                                    </>
                                )}
                            </button>

                            <button 
                                className="btn-download secondary"
                                onClick={handleGenerateReport}
                                disabled={downloading}
                            >
                                Download Tuning Report
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="download-success">
                        <div className="success-icon">✅</div>
                        <h3>Download Complete!</h3>
                        <p>Your optimized tune has been downloaded successfully.</p>
                        <div className="next-steps">
                            <h4>Next Steps:</h4>
                            <ol>
                                <li>Flash the tune using your preferred tool</li>
                                <li>Take initial test drives carefully</li>
                                <li>Monitor engine parameters closely</li>
                                <li>Provide feedback on the results</li>
                            </ol>
                        </div>
                    </div>
                )}
            </div>

            <div className="safety-reminder">
                <h4>Safety Reminder</h4>
                <p>
                    Always start with conservative settings and gradually increase performance 
                    modifications. Monitor your engine closely and revert to stock tune if 
                    any issues arise.
                </p>
            </div>
        </div>
    );
}

export default ExportDownloadPanel;
