import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import AnalysisViewer from './components/AnalysisViewer';
import SuggestionsPanel from './components/SuggestionsPanel';
import TuneDiffViewer from './components/TuneDiffViewer';
import ExportDownloadPanel from './components/ExportDownloadPanel';
import FeedbackPanel from './components/FeedbackPanel';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
    const [currentStep, setCurrentStep] = useState('upload');
    const [sessionId, setSessionId] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [selectedChanges, setSelectedChanges] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handlePackageUpload = (uploadResult) => {
        setSessionId(uploadResult.session_id);
        setCurrentStep('analyze');
        analyzePackage(uploadResult.session_id);
    };

    const analyzePackage = async (sessionId) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/analyze_package', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer demo_token`
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📊 Analysis Response:', data); // Debug log

            setAnalysisData(data);
            setCurrentStep('suggestions');
        } catch (err) {
            console.error('❌ Analysis Error:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestionsReview = (changes) => {
        setSelectedChanges(changes);
        setCurrentStep('diff');
    };

    const handleDiffApproval = () => {
        setCurrentStep('apply');
        applyChanges();
    };

    const applyChanges = async () => {
        setLoading(true);

        try {
            const response = await fetch('/api/apply_changes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer demo_token`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    selected_changes: selectedChanges
                })
            });

            if (!response.ok) {
                throw new Error(`Apply changes failed: ${response.statusText}`);
            }

            const data = await response.json();
            setCurrentStep('download');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadComplete = () => {
        setCurrentStep('feedback');
    };

    const handleFeedbackSubmit = () => {
        // Reset for new session
        setCurrentStep('upload');
        setSessionId(null);
        setAnalysisData(null);
        setSelectedChanges([]);
        setError(null);
    };

    // Extract suggestions from analysis data with proper fallbacks
    const getSuggestions = () => {
        if (!analysisData) return [];

        // Try multiple possible locations for suggestions
        return analysisData.detailed_data?.suggestions ||
            analysisData.legacy_compatibility?.suggestions ||
            analysisData.suggestions ||
            [];
    };

    const renderCurrentStep = () => {
        if (loading) {
            return <LoadingSpinner message="Processing your tune package..." />;
        }

        if (error) {
            return (
                <div className="error-container">
                    <h2>❌ Error</h2>
                    <p>{error}</p>
                    <button className="btn btn-primary" onClick={() => setError(null)}>Try Again</button>

                    {/* Debug info in development */}
                    {process.env.NODE_ENV === 'development' && analysisData && (
                        <details style={{ marginTop: '20px', textAlign: 'left' }}>
                            <summary>🔧 Debug: Last Analysis Data</summary>
                            <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '300px' }}>
                                {JSON.stringify(analysisData, null, 2)}
                            </pre>
                        </details>
                    )}
                </div>
            );
        }

        switch (currentStep) {
            case 'upload':
                return <FileUpload onPackageUpload={handlePackageUpload} />;

            case 'analyze':
                return <LoadingSpinner message="Analyzing your datalog and tune..." />;

            case 'suggestions':
                const suggestions = getSuggestions();
                console.log('🤖 Suggestions found:', suggestions.length); // Debug log

                return (
                    <div>
                        <AnalysisViewer data={analysisData} />
                        <SuggestionsPanel
                            suggestions={suggestions}
                            onReview={handleSuggestionsReview}
                        />

                        {/* Debug panel for development */}
                        {process.env.NODE_ENV === 'development' && (
                            <div className="debug-panel" style={{
                                margin: '20px 0',
                                padding: '15px',
                                background: '#f8f9fa',
                                border: '1px solid #dee2e6',
                                borderRadius: '5px'
                            }}>
                                <h4>🔧 Debug Info</h4>
                                <p><strong>Analysis Type:</strong> {analysisData?.analysis_type || 'unknown'}</p>
                                <p><strong>Platform:</strong> {analysisData?.platform || 'unknown'}</p>
                                <p><strong>Suggestions Found:</strong> {suggestions.length}</p>
                                <p><strong>Enhanced Analysis:</strong> {analysisData?.metadata?.enhanced_features_used ? 'Yes' : 'No'}</p>

                                <details>
                                    <summary>Raw Suggestions Data</summary>
                                    <pre style={{ fontSize: '11px', maxHeight: '200px', overflow: 'auto' }}>
                                        {JSON.stringify(suggestions, null, 2)}
                                    </pre>
                                </details>
                            </div>
                        )}
                    </div>
                );

            case 'diff':
                return (
                    <TuneDiffViewer
                        sessionId={sessionId}
                        selectedChanges={selectedChanges}
                        onApproval={handleDiffApproval}
                    />
                );

            case 'apply':
                return <LoadingSpinner message="Applying changes to your tune..." />;

            case 'download':
                return (
                    <ExportDownloadPanel
                        sessionId={sessionId}
                        onDownloadComplete={handleDownloadComplete}
                    />
                );

            case 'feedback':
                return (
                    <FeedbackPanel
                        sessionId={sessionId}
                        onSubmit={handleFeedbackSubmit}
                    />
                );

            default:
                return <FileUpload onPackageUpload={handlePackageUpload} />;
        }
    };

    return (
        <ErrorBoundary>
            <div className="App">
                <header className="App-header">
                    <div className="container">
                        <h1>🏎️ ECU Tuning Assistant</h1>
                        <div className="progress-indicator">
                            <div className={`step ${currentStep === 'upload' ? 'active' : ''}`}>Upload</div>
                            <div className={`step ${currentStep === 'suggestions' ? 'active' : ''}`}>Analysis</div>
                            <div className={`step ${currentStep === 'diff' ? 'active' : ''}`}>Review</div>
                            <div className={`step ${currentStep === 'download' ? 'active' : ''}`}>Download</div>
                            <div className={`step ${currentStep === 'feedback' ? 'active' : ''}`}>Feedback</div>
                        </div>
                    </div>
                </header>

                <main className="App-main">
                    <div className="container">
                        {renderCurrentStep()}
                    </div>
                </main>

                <footer className="App-footer">
                    <div className="container">
                        <p>© 2025 ECU Tuning Assistant - Professional Grade Tuning Software</p>
                        {process.env.NODE_ENV === 'development' && (
                            <p style={{ fontSize: '12px', opacity: 0.7 }}>
                                🔧 Development Mode - Debug info enabled
                            </p>
                        )}
                    </div>
                </footer>
            </div>
        </ErrorBoundary>
    );
}

export default App;