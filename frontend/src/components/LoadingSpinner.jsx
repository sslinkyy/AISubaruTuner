
import React from 'react';

function LoadingSpinner({ message = "Loading..." }) {
    return (
        <div className="loading-spinner">
            <div className="spinner"></div>
            <p>{message}</p>
        </div>
    );
}

export default LoadingSpinner;
