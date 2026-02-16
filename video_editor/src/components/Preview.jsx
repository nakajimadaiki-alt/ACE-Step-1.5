import React from 'react';
import '../styles/Preview.css';

const Preview = ({ currentFrame, children }) => {
    return (
        <div className="preview-container">
            <div className="canvas-wrapper">
                <div className="canvas">
                    {children}
                    <div className="frame-overlay">
                        フレーム: {currentFrame}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Preview;
