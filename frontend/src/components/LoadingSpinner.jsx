
import React from 'react';

function LoadingSpinner({ message = "Loading..." }) {
    return (
        <div className="loading-spinner" role="status" aria-live="polite">
            <div className="spinner" aria-hidden="true"></div>
            <p>{message}</p>
        </div>
    );
}

export default LoadingSpinner;
