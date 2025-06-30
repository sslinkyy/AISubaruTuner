import React, { useState } from 'react';
import './FileUpload.css';

function FileUpload({ onPackageUpload }) {
    const [datalog, setDatalog] = useState(null);
    const [tune, setTune] = useState(null);
    const [definition, setDefinition] = useState(null); // New state for XML definition
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [dragOver, setDragOver] = useState(false);
    const [uploadProgress, setUploadProgress] = useState('');

    const handleDatalogSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            validateDatalogFile(file);
        }
    };

    const handleTuneSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            validateTuneFile(file);
        }
    };

    const handleDefinitionSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            validateDefinitionFile(file);
        }
    };

    const validateDatalogFile = (file) => {
        const validExtensions = ['.csv', '.log'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

        if (!validExtensions.includes(extension)) {
            setError('Invalid datalog file. Please select a .csv or .log file.');
            return;
        }

        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            setError('Datalog file too large. Maximum size is 50MB.');
            return;
        }

        setDatalog(file);
        setError('');
    };

    const validateTuneFile = (file) => {
        const validExtensions = ['.bin', '.hex', '.rom'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

        if (!validExtensions.includes(extension)) {
            setError('Invalid tune file. Please select a .bin, .hex, or .rom file.');
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            setError('Tune file too large. Maximum size is 10MB.');
            return;
        }

        setTune(file);
        setError('');
    };

    const validateDefinitionFile = (file) => {
        const validExtensions = ['.xml'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

        if (!validExtensions.includes(extension)) {
            setError('Invalid XML definition file. Please select a .xml file.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            setError('XML definition file too large. Maximum size is 5MB.');
            return;
        }

        setDefinition(file);
        setError('');
    };

    const handleDrop = (e, type) => {
        e.preventDefault();
        setDragOver(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            if (type === 'datalog') {
                validateDatalogFile(files[0]);
            } else if (type === 'tune') {
                validateTuneFile(files[0]);
            } else if (type === 'definition') {
                validateDefinitionFile(files[0]);
            }
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setDragOver(false);
    };

    const handleUpload = async () => {
        if (!datalog || !tune) {
            setError('Please select both a datalog and a tune file.');
            return;
        }

        setUploading(true);
        setError('');
        setUploadProgress('Uploading files...');

        const formData = new FormData();
        formData.append('datalog', datalog);
        formData.append('tune', tune);
        if (definition) {
            formData.append('definition', definition);
        }

        try {
            // Step 1: Upload the package
            const uploadResponse = await fetch('http://localhost:8000/api/upload_package', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer demo_token'
                },
                body: formData
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json().catch(() => ({}));
                throw new Error(errorData.detail || `Upload failed: ${uploadResponse.statusText}`);
            }

            const uploadResult = await uploadResponse.json();
            setUploadProgress('Files uploaded successfully! Analyzing...');

            // Step 2: Analyze the uploaded package
            const analysisResponse = await fetch('http://localhost:8000/api/analyze_package', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer demo_token'
                },
                body: JSON.stringify({ session_id: uploadResult.session_id })
            });

            if (!analysisResponse.ok) {
                const errorData = await analysisResponse.json().catch(() => ({}));
                throw new Error(errorData.detail || `Analysis failed: ${analysisResponse.statusText}`);
            }

            const analysisResult = await analysisResponse.json();
            setUploadProgress('Analysis complete!');

            // Combine upload and analysis results
            const completeResult = {
                ...uploadResult,
                analysis: analysisResult
            };

            // Pass results to parent component
            onPackageUpload(completeResult);

            // Reset form after successful upload
            setTimeout(() => {
                setDatalog(null);
                setTune(null);
                setDefinition(null);
                setUploadProgress('');
            }, 2000);

        } catch (err) {
            console.error('Upload/Analysis error:', err);
            setError('Upload failed: ' + err.message);
            setUploadProgress('');
        } finally {
            setUploading(false);
        }
    };

    const resetFiles = () => {
        setDatalog(null);
        setTune(null);
        setDefinition(null);
        setError('');
        setUploadProgress('');
    };

    return (
        <div className="file-upload">
            <div className="upload-header">
                <h2>Upload Your Tune Package</h2>
                <p>Upload your datalog, tune file, and optionally an XML definition file for comprehensive analysis</p>
            </div>

            <div className="upload-grid">
                <div
                    className={`upload-zone datalog-zone ${dragOver ? 'drag-over' : ''}`}
                    onDrop={(e) => handleDrop(e, 'datalog')}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                >
                    <div className="upload-icon">📊</div>
                    <h3>Datalog File</h3>
                    <p>CSV or LOG format</p>
                    <input
                        type="file"
                        accept=".csv,.log"
                        onChange={handleDatalogSelect}
                        disabled={uploading}
                        id="datalog-input"
                        style={{ display: 'none' }}
                    />
                    <label htmlFor="datalog-input" className="file-select-btn">
                        Select Datalog
                    </label>
                    {datalog && (
                        <div className="file-info">
                            <div className="file-name">{datalog.name}</div>
                            <div className="file-size">
                                {(datalog.size / 1024 / 1024).toFixed(2)} MB
                            </div>
                            <div className="file-status">✅ Ready</div>
                        </div>
                    )}
                </div>

                <div
                    className={`upload-zone tune-zone ${dragOver ? 'drag-over' : ''}`}
                    onDrop={(e) => handleDrop(e, 'tune')}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                >
                    <div className="upload-icon">⚙️</div>
                    <h3>Tune File</h3>
                    <p>BIN, HEX, or ROM format</p>
                    <input
                        type="file"
                        accept=".bin,.hex,.rom"
                        onChange={handleTuneSelect}
                        disabled={uploading}
                        id="tune-input"
                        style={{ display: 'none' }}
                    />
                    <label htmlFor="tune-input" className="file-select-btn">
                        Select Tune
                    </label>
                    {tune && (
                        <div className="file-info">
                            <div className="file-name">{tune.name}</div>
                            <div className="file-size">
                                {(tune.size / 1024).toFixed(2)} KB
                            </div>
                            <div className="file-status">✅ Ready</div>
                        </div>
                    )}
                </div>

                <div
                    className={`upload-zone definition-zone ${dragOver ? 'drag-over' : ''}`}
                    onDrop={(e) => handleDrop(e, 'definition')}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                >
                    <div className="upload-icon">📄</div>
                    <h3>XML Definition File (Optional)</h3>
                    <p>Upload XML file describing your ROM tables</p>
                    <input
                        type="file"
                        accept=".xml"
                        onChange={handleDefinitionSelect}
                        disabled={uploading}
                        id="definition-input"
                        style={{ display: 'none' }}
                    />
                    <label htmlFor="definition-input" className="file-select-btn">
                        Select XML Definition
                    </label>
                    {definition && (
                        <div className="file-info">
                            <div className="file-name">{definition.name}</div>
                            <div className="file-size">
                                {(definition.size / 1024).toFixed(2)} KB
                            </div>
                            <div className="file-status">✅ Ready</div>
                        </div>
                    )}
                </div>
            </div>

            {error && <div className="error-message">❌ {error}</div>}
            {uploadProgress && <div className="progress-message">🔄 {uploadProgress}</div>}

            <div className="upload-actions">
                <button
                    className="upload-btn"
                    onClick={handleUpload}
                    disabled={!datalog || !tune || uploading}
                >
                    {uploading ? '🔄 Uploading & Analyzing...' : '🚀 Upload & Analyze'}
                </button>

                {(datalog || tune || definition) && !uploading && (
                    <button
                        className="reset-btn"
                        onClick={resetFiles}
                    >
                        🗑️ Clear Files
                    </button>
                )}
            </div>

            <div className="upload-info">
                <h4>What happens next?</h4>
                <div className="info-steps">
                    <div className="info-step">
                        <span className="step-number">1</span>
                        <span>Platform detection (Subaru/Hondata)</span>
                    </div>
                    <div className="info-step">
                        <span className="step-number">2</span>
                        <span>Datalog analysis for issues</span>
                    </div>
                    <div className="info-step">
                        <span className="step-number">3</span>
                        <span>AI-powered tuning suggestions</span>
                    </div>
                    <div className="info-step">
                        <span className="step-number">4</span>
                        <span>Safety validation checks</span>
                    </div>
                    <div className="info-step">
                        <span className="step-number">5</span>
                        <span>Optimized tune generation</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default FileUpload;