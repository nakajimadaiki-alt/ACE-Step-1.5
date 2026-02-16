import React from 'react';

const ExampleScene = ({ currentFrame }) => {
    // 30FPS baseline
    const progress = Math.min(currentFrame / 150, 1);

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: '#050505' }}>
            {/* Background circles */}
            {[...Array(5)].map((_, i) => (
                <div
                    key={i}
                    style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        width: '300px',
                        height: '300px',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: '50%',
                        transform: `translate(-50%, -50%) scale(${0.5 + i * 0.2 + Math.sin(currentFrame * 0.05 + i) * 0.1})`,
                        opacity: 1 - (i * 0.2),
                    }}
                />
            ))}

            {/* Rotating segments */}
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: '400px',
                height: '400px',
                border: '4px dashed #3b82f6',
                borderRadius: '50%',
                transform: `translate(-50%, -50%) rotate(${currentFrame * 2}deg)`,
                opacity: Math.max(0, Math.min(1, currentFrame / 30))
            }} />

            {/* Main Title appearing */}
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: `translate(-50%, -50%)`,
                textAlign: 'center'
            }}>
                <h1 style={{
                    fontSize: '64px',
                    margin: 0,
                    opacity: progress > 0.2 ? Math.min(1, (progress - 0.2) * 5) : 0,
                    transform: `translateY(${(1 - progress) * 50}px)`,
                    background: 'linear-gradient(45deg, #3b82f6, #60a5fa)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                }}>
                    モーショングラフィックス
                </h1>
                <p style={{
                    fontSize: '24px',
                    color: '#9ca3af',
                    opacity: progress > 0.5 ? Math.min(1, (progress - 0.5) * 5) : 0,
                }}>
                    Reactでつくる次世代動画制作
                </p>
            </div>

            {/* Progress Bar */}
            <div style={{
                position: 'absolute',
                bottom: '100px',
                left: '20%',
                width: '60%',
                height: '4px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '2px',
                overflow: 'hidden'
            }}>
                <div style={{
                    width: `${progress * 100}%`,
                    height: '100%',
                    background: '#3b82f6',
                    boxShadow: '0 0 10px #3b82f6'
                }} />
            </div>
        </div>
    );
};

export default ExampleScene;
