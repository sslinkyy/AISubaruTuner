import React, { useState } from 'react';
import './SuggestionsPanel.css';

function SuggestionsPanel({ suggestions, onReview }) {
    const [selectedSuggestions, setSelectedSuggestions] = useState([]);
    const [expandedSuggestion, setExpandedSuggestion] = useState(null);

    const handleSuggestionToggle = (suggestionId) => {
        setSelectedSuggestions(prev => {
            if (prev.includes(suggestionId)) {
                return prev.filter(id => id !== suggestionId);
            } else {
                return [...prev, suggestionId];
            }
        });
    };

    const handleSelectAll = () => {
        if (selectedSuggestions.length === suggestions.length) {
            setSelectedSuggestions([]);
        } else {
            setSelectedSuggestions(suggestions.map((s, index) => s.id || index));
        }
    };

    const handleReview = () => {
        onReview(selectedSuggestions);
    };

    const getPriorityColor = (priority) => {
        const safePriority = (priority || '').toLowerCase();
        switch (safePriority) {
            case 'critical': return '#dc3545';
            case 'high': return '#fd7e14';
            case 'medium': return '#ffc107';
            case 'low': return '#28a745';
            default: return '#6c757d';
        }
    };

    const getPriorityIcon = (priority) => {
        const safePriority = (priority || '').toLowerCase();
        switch (safePriority) {
            case 'critical': return '🚨';
            case 'high': return '⚠️';
            case 'medium': return '💡';
            case 'low': return '✨';
            default: return '📝';
        }
    };

    // Safe access helper function
    const safeGet = (obj, key, fallback = 'N/A') => {
        return obj && obj[key] !== undefined && obj[key] !== null ? obj[key] : fallback;
    };

    if (!suggestions || suggestions.length === 0) {
        return (
            <div className="suggestions-panel">
                <div className="suggestions-header">
                    <h2>🤖 AI Tuning Suggestions</h2>
                </div>
                <div className="no-suggestions">
                    <h3>✅ No Suggestions Needed</h3>
                    <p>Your tune appears to be well-optimized based on the datalog analysis. No immediate changes are recommended.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="suggestions-panel">
            <div className="suggestions-header">
                <h2>🤖 AI Tuning Suggestions</h2>
                <p>Review and select the tuning changes you'd like to apply</p>

                <div className="suggestions-controls">
                    <button 
                        className="btn-select-all"
                        onClick={handleSelectAll}
                    >
                        {selectedSuggestions.length === suggestions.length ? 'Deselect All' : 'Select All'}
                    </button>
                    <span className="selection-count">
                        {selectedSuggestions.length} of {suggestions.length} selected
                    </span>
                </div>
            </div>

            <div className="suggestions-list">
                {suggestions.map((suggestion, index) => {
                    // Use index as fallback ID if suggestion.id is missing
                    const suggestionId = suggestion.id || index;

                    return (
                        <div 
                            key={suggestionId} 
                            className={`suggestion-item ${selectedSuggestions.includes(suggestionId) ? 'selected' : ''}`}
                        >
                            <div className="suggestion-header">
                                <div className="suggestion-main">
                                    <input
                                        type="checkbox"
                                        checked={selectedSuggestions.includes(suggestionId)}
                                        onChange={() => handleSuggestionToggle(suggestionId)}
                                        className="suggestion-checkbox"
                                    />
                                    <div className="suggestion-info">
                                        <div className="suggestion-title">
                                            <span className="suggestion-icon">
                                                {getPriorityIcon(suggestion.priority)}
                                            </span>
                                            <span className="suggestion-type">
                                                {safeGet(suggestion, 'type', 'Unknown')}
                                            </span>
                                            <span 
                                                className="priority-badge"
                                                style={{ backgroundColor: getPriorityColor(suggestion.priority) }}
                                            >
                                                {(suggestion.priority || 'unknown').toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="suggestion-description">
                                            {safeGet(suggestion, 'description', 'No description available')}
                                        </p>
                                        {/* Fallback for message field if description is not available */}
                                        {!suggestion.description && suggestion.message && (
                                            <p className="suggestion-description">
                                                {suggestion.message}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button
                                    className="expand-btn"
                                    onClick={() => setExpandedSuggestion(
                                        expandedSuggestion === suggestionId ? null : suggestionId
                                    )}
                                >
                                    {expandedSuggestion === suggestionId ? '▼' : '▶'}
                                </button>
                            </div>

                            {expandedSuggestion === suggestionId && (
                                <div className="suggestion-details">
                                    <div className="detail-grid">
                                        <div className="detail-item">
                                            <strong>Parameter:</strong> {safeGet(suggestion, 'parameter')}
                                        </div>
                                        <div className="detail-item">
                                            <strong>Change Type:</strong> {safeGet(suggestion, 'change_type')}
                                        </div>
                                        {suggestion.percentage !== undefined && suggestion.percentage !== null && (
                                            <div className="detail-item">
                                                <strong>Adjustment:</strong> {suggestion.percentage}%
                                            </div>
                                        )}
                                        {suggestion.degrees !== undefined && suggestion.degrees !== null && (
                                            <div className="detail-item">
                                                <strong>Timing Change:</strong> {suggestion.degrees}°
                                            </div>
                                        )}
                                        <div className="detail-item">
                                            <strong>Affected Areas:</strong> {safeGet(suggestion, 'affected_areas')}
                                        </div>
                                        {/* Additional fields that might be present */}
                                        {suggestion.rpm_range && (
                                            <div className="detail-item">
                                                <strong>RPM Range:</strong> {suggestion.rpm_range}
                                            </div>
                                        )}
                                        {suggestion.load_range && (
                                            <div className="detail-item">
                                                <strong>Load Range:</strong> {suggestion.load_range}
                                            </div>
                                        )}
                                    </div>

                                    <div className="impact-analysis">
                                        <div className="impact-item safety">
                                            <strong>Safety Impact:</strong> {safeGet(suggestion, 'safety_impact')}
                                        </div>
                                        <div className="impact-item performance">
                                            <strong>Performance Impact:</strong> {safeGet(suggestion, 'performance_impact')}
                                        </div>
                                        {/* Additional impact fields */}
                                        {suggestion.confidence && (
                                            <div className="impact-item confidence">
                                                <strong>Confidence:</strong> {suggestion.confidence}
                                            </div>
                                        )}
                                        {suggestion.expected_improvement && (
                                            <div className="impact-item improvement">
                                                <strong>Expected Improvement:</strong> {suggestion.expected_improvement}
                                            </div>
                                        )}
                                    </div>

                                    {/* Show raw suggestion data for debugging if needed */}
                                    {process.env.NODE_ENV === 'development' && (
                                        <div className="debug-info">
                                            <details>
                                                <summary>Debug Info (Dev Only)</summary>
                                                <pre>{JSON.stringify(suggestion, null, 2)}</pre>
                                            </details>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="suggestions-actions">
                <button 
                    className="btn-review"
                    onClick={handleReview}
                    disabled={selectedSuggestions.length === 0}
                >
                    Review Selected Changes ({selectedSuggestions.length})
                </button>

                {/* Additional action buttons */}
                <button 
                    className="btn-export"
                    onClick={() => {
                        const selectedData = suggestions.filter((s, i) => 
                            selectedSuggestions.includes(s.id || i)
                        );
                        console.log('Selected suggestions:', selectedData);
                        // You can add export functionality here
                    }}
                    disabled={selectedSuggestions.length === 0}
                >
                    Export Selected
                </button>
            </div>

            {/* Summary stats */}
            <div className="suggestions-summary">
                <div className="summary-stats">
                    <div className="stat-item">
                        <span className="stat-label">Total Suggestions:</span>
                        <span className="stat-value">{suggestions.length}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Critical:</span>
                        <span className="stat-value critical">
                            {suggestions.filter(s => (s.priority || '').toLowerCase() === 'critical').length}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">High Priority:</span>
                        <span className="stat-value high">
                            {suggestions.filter(s => (s.priority || '').toLowerCase() === 'high').length}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Selected:</span>
                        <span className="stat-value selected">
                            {selectedSuggestions.length}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SuggestionsPanel;