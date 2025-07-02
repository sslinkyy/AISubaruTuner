import React from 'react';
import SuggestionsPanel from './SuggestionsPanel';
import './TuneSuggestionsReview.css';

function TuneSuggestionsReview({ analysis, onReview = () => {} }) {
    if (!analysis) return null;

    const {
        status = 'unknown',
        session_id,
        platform,
        analysis_type,
        timestamp,
        ai_suggestions = [],
        message,
        debug
    } = analysis;

    const formatTime = (ts) => ts ? new Date(ts).toLocaleString() : 'N/A';

    return (
        <div className="tune-suggestions-review">
            <div className="analysis-summary">
                <h3>Tune Analysis Summary</h3>
                <div className="summary-grid">
                    <div className="summary-item"><strong>Session:</strong> {session_id}</div>
                    <div className="summary-item"><strong>Platform:</strong> {platform || 'Unknown'}</div>
                    <div className="summary-item"><strong>Type:</strong> {analysis_type}</div>
                    <div className="summary-item"><strong>Status:</strong> {status}</div>
                    <div className="summary-item"><strong>Time:</strong> {formatTime(timestamp)}</div>
                </div>
            </div>

            {status !== 'success' && message && (
                <div className="analysis-error">
                    <p>{message}</p>
                </div>
            )}

            <SuggestionsPanel suggestions={ai_suggestions} onReview={onReview} />

            {debug && process.env.NODE_ENV === 'development' && (
                <div className="debug-section">
                    <details>
                        <summary>Debug Info</summary>
                        <pre>{JSON.stringify(debug, null, 2)}</pre>
                    </details>
                </div>
            )}
        </div>
    );
}

export default TuneSuggestionsReview;
