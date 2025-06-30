
import React, { useState } from 'react';
import './FeedbackPanel.css';

function FeedbackPanel({ sessionId, onSubmit }) {
    const [rating, setRating] = useState(0);
    const [comments, setComments] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState(null);

    const handleRatingClick = (value) => {
        setRating(value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (rating === 0) {
            setError('Please provide a rating before submitting.');
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer demo_token'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    rating,
                    comments
                })
            });

            if (!response.ok) {
                throw new Error(`Feedback submission failed: ${response.statusText}`);
            }

            setSubmitted(true);
            setTimeout(() => {
                onSubmit();
            }, 3000);

        } catch (err) {
            setError(err.message);
        } finally {
            setSubmitting(false);
        }
    };

    const getRatingText = (rating) => {
        switch (rating) {
            case 1: return 'Poor';
            case 2: return 'Fair';
            case 3: return 'Good';
            case 4: return 'Very Good';
            case 5: return 'Excellent';
            default: return 'Select Rating';
        }
    };

    if (submitted) {
        return (
            <div className="feedback-panel">
                <div className="feedback-success">
                    <div className="success-icon">🎉</div>
                    <h2>Thank You for Your Feedback!</h2>
                    <p>Your feedback helps us improve the ECU Tuning Assistant.</p>
                    <div className="success-message">
                        <p>You'll be redirected to start a new session shortly...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="feedback-panel">
            <div className="feedback-header">
                <h2>📝 Share Your Experience</h2>
                <p>Help us improve by sharing your feedback on the tuning process</p>
            </div>

            <form onSubmit={handleSubmit} className="feedback-form">
                <div className="rating-section">
                    <h3>How would you rate your experience?</h3>
                    <div className="star-rating">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                type="button"
                                className={`star ${star <= rating ? 'active' : ''}`}
                                onClick={() => handleRatingClick(star)}
                                disabled={submitting}
                            >
                                ⭐
                            </button>
                        ))}
                    </div>
                    <div className="rating-text">
                        {getRatingText(rating)}
                    </div>
                </div>

                <div className="comments-section">
                    <h3>Additional Comments (Optional)</h3>
                    <textarea
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        placeholder="Tell us about your experience, suggestions for improvement, or any issues you encountered..."
                        rows={6}
                        disabled={submitting}
                        className="comments-textarea"
                    />
                </div>

                <div className="feedback-questions">
                    <h3>Quick Questions</h3>
                    <div className="question-grid">
                        <div className="question-item">
                            <span className="question">Was the analysis accurate?</span>
                            <div className="quick-rating">
                                <button type="button" className="quick-btn positive">👍</button>
                                <button type="button" className="quick-btn negative">👎</button>
                            </div>
                        </div>
                        <div className="question-item">
                            <span className="question">Were suggestions helpful?</span>
                            <div className="quick-rating">
                                <button type="button" className="quick-btn positive">👍</button>
                                <button type="button" className="quick-btn negative">👎</button>
                            </div>
                        </div>
                        <div className="question-item">
                            <span className="question">Easy to use interface?</span>
                            <div className="quick-rating">
                                <button type="button" className="quick-btn positive">👍</button>
                                <button type="button" className="quick-btn negative">👎</button>
                            </div>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="error-message">
                        ❌ {error}
                    </div>
                )}

                <div className="feedback-actions">
                    <button 
                        type="submit" 
                        className="btn-submit"
                        disabled={submitting || rating === 0}
                    >
                        {submitting ? (
                            <>
                                <span className="spinner-small"></span>
                                Submitting...
                            </>
                        ) : (
                            'Submit Feedback'
                        )}
                    </button>

                    <button 
                        type="button" 
                        className="btn-skip"
                        onClick={onSubmit}
                        disabled={submitting}
                    >
                        Skip Feedback
                    </button>
                </div>
            </form>

            <div className="privacy-notice">
                <p>
                    <strong>Privacy:</strong> Your feedback is anonymous and used solely to improve 
                    our service. No personal information is stored with your feedback.
                </p>
            </div>
        </div>
    );
}

export default FeedbackPanel;
