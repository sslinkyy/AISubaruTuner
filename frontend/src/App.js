import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import AnalysisViewer from './components/AnalysisViewer';
import TuneSuggestionsReview from './components/TuneSuggestionsReview';
import TuneDiffViewer from './components/TuneDiffViewer';
import TuneTableComparison from './components/TuneTableComparison';
import TuneInfoPanel from './components/TuneInfoPanel';
import SessionContextPanel from './components/SessionContextPanel';
import ExportDownloadPanel from './components/ExportDownloadPanel';
import FeedbackPanel from './components/FeedbackPanel';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';
import TableTreeViewer from './components/TableTreeViewer';
import DebugViewer from './components/DebugViewer';

function App() {
    const [currentStep, setCurrentStep] = useState('upload');
    const [sessionId, setSessionId] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [selectedChanges, setSelectedChanges] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [comparisonTables, setComparisonTables] = useState([]);
    const [rawTables, setRawTables] = useState(null);
    const [debugData, setDebugData] = useState(null);

    const handlePackageUpload = async (uploadResult) => {
        setSessionId(uploadResult.session_id);
        await fetchRawTables(uploadResult.session_id);
        setCurrentStep('tables');
    };

    const fetchRawTables = async (sessionId) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/session/${sessionId}/raw_tables`, {
                headers: { 'Authorization': `Bearer demo_token` }
            });
            if (response.ok) {
                const data = await response.json();
                setRawTables(data.tables || {});
            }
        } catch (err) {
            console.error('Raw table fetch failed', err);
        } finally {
            setLoading(false);
        }
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
            console.log('Analysis Response:', data); // Debug log

            setAnalysisData(data);
            setCurrentStep('suggestions');
        } catch (err) {
            console.error('Analysis Error:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestionsReview = (changes) => {
        setSelectedChanges(changes);
        setCurrentStep('diff');
    };

    const handleDiffApproval = async () => {
        setCurrentStep('apply');
        await applyChanges();
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
                let errDetail = response.statusText;
                try {
                    const msg = await response.json();
                    errDetail = msg.detail || msg.message || errDetail;
                } catch (_) { }
                throw new Error(`Apply changes failed: ${errDetail}`);
            }

            const data = await response.json();
            if (data.tables && data.tables.length > 0) {
                setComparisonTables(data.tables);
                setCurrentStep('comparison');
            } else {
                setError('No table changes were generated for the selected suggestions.');
                setCurrentStep('diff');
            }
        } catch (err) {
            setCurrentStep('diff');
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    const handleDownloadComplete = () => {
        setCurrentStep('feedback');
    };

    const handleShowDebug = async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`/api/session/${sessionId}/debug_data`, {
                headers: { 'Authorization': `Bearer demo_token` }
            });
            if (res.ok) {
                const data = await res.json();
                setDebugData(data);
                setCurrentStep('debug');
            }
        } catch (err) {
            console.error('Debug fetch failed', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedbackSubmit = () => {
        // Reset for new session
        setCurrentStep('upload');
        setSessionId(null);
        setAnalysisData(null);
        setSelectedChanges([]);
        setComparisonTables([]);
        setRawTables(null);
        setDebugData(null);
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
                    <h2>Error</h2>
                    <p>{error}</p>
                    <button className="btn btn-primary" onClick={() => setError(null)}>Try Again</button>

                    {/* Debug info in development */}
                    {process.env.NODE_ENV === 'development' && analysisData && (
                        <details style={{ marginTop: '20px', textAlign: 'left' }}>
                            <summary>Debug: Last Analysis Data</summary>
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

            case 'tables':
                return (
                    <TableTreeViewer
                        tables={rawTables || {}}
                        onContinue={() => {
                            setCurrentStep('analyze');
                            analyzePackage(sessionId);
                        }}
                    />
                );

            case 'analyze':
                return <LoadingSpinner message="Analyzing your datalog and tune..." />;

            case 'suggestions':
                const suggestions = getSuggestions();
                return (
                    <div>
                        <SessionContextPanel
                            vehicle={analysisData?.vehicle_info}
                            session={analysisData?.session_info}
                        />
                        <TuneInfoPanel
                            romAnalysis={analysisData?.rom_analysis}
                            metadata={analysisData?.analysis_metadata}
                            tuneFile={analysisData?.file_info?.tune}
                        />
                        <AnalysisViewer data={analysisData} />
                        <TuneSuggestionsReview
                            analysis={analysisData}
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
                                <h4>Debug Info</h4>
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
                        analysisData={analysisData}
                        selectedChanges={selectedChanges}
                        onApproval={handleDiffApproval}
                    />
                );

            case 'apply':
                return <LoadingSpinner message="Applying changes to your tune..." />;

            case 'comparison':
                return (
                    <TuneTableComparison
                        tables={comparisonTables}
                        onContinue={() => setCurrentStep('download')}
                    />
                );

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

            case 'debug':
                return <DebugViewer data={debugData} onBack={() => setCurrentStep('feedback')} />;

            default:
                return <FileUpload onPackageUpload={handlePackageUpload} />;
        }
    };

    return (
        <ErrorBoundary>
            <div className="App">
                <header className="App-header">
                    <div className="container">
                        <h1>ECU Tuning Assistant</h1>
                        <div className="progress-indicator">
                            <div className={`step ${currentStep === 'upload' ? 'active' : ''}`}>Upload</div>
                            <div className={`step ${currentStep === 'tables' ? 'active' : ''}`}>Tables</div>
                            <div className={`step ${currentStep === 'suggestions' ? 'active' : ''}`}>Analysis</div>
                            <div className={`step ${currentStep === 'diff' ? 'active' : ''}`}>Review</div>
                            <div className={`step ${currentStep === 'comparison' ? 'active' : ''}`}>Compare</div>
                            <div className={`step ${currentStep === 'download' ? 'active' : ''}`}>Download</div>
                            <div className={`step ${currentStep === 'feedback' ? 'active' : ''}`}>Feedback</div>
                            <div className={`step ${currentStep === 'debug' ? 'active' : ''}`}>Debug</div>
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
                                Development Mode - Debug info enabled
                            </p>
                        )}
                        {analysisData && (
                            <button className="btn btn-secondary" onClick={handleShowDebug} style={{ marginLeft: '10px' }}>
                                View Debug Info
                            </button>
                        )}
                    </div>
                </footer>
            </div>
        </ErrorBoundary>
    );
}

export default App;