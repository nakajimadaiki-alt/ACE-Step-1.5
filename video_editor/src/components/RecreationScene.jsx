import React from 'react';

const RecreationScene = ({ currentFrame }) => {
    // 30FPS baseline. Intro segments:
    // 0-30f: Title fade in & slide up
    // 30-150f: Subtext appears, background moves

    const titleProgress = Math.min(Math.max((currentFrame - 0) / 20, 0), 1);
    const subtextProgress = Math.min(Math.max((currentFrame - 20) / 15, 0), 1);
    const frameScale = 1 + (currentFrame * 0.0005);

    return (
        <div style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            overflow: 'hidden',
            background: '#000',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            {/* Moving Grid Background (simulating FrameScript feel) */}
            <div style={{
                position: 'absolute',
                width: '200%',
                height: '200%',
                backgroundImage: `
          linear-gradient(to right, #111 1px, transparent 1px),
          linear-gradient(to bottom, #111 1px, transparent 1px)
        `,
                backgroundSize: '40px 40px',
                transform: `rotate(15deg) translate(${-currentFrame * 0.5}px, ${-currentFrame * 0.5}px) scale(${frameScale})`,
                opacity: 0.5
            }} />

            {/* Blue Glow */}
            <div style={{
                position: 'absolute',
                width: '600px',
                height: '600px',
                background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                pointerEvents: 'none'
            }} />

            {/* Main Title: 動画編集ソフト作ってみた！ */}
            <div style={{
                opacity: titleProgress,
                transform: `translateY(${(1 - titleProgress) * 30}px)`,
                fontSize: '72px',
                fontWeight: 'bold',
                color: '#fff',
                zIndex: 10,
                textShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
            }}>
                動画編集ソフト作ってみた！
            </div>

            {/* Sub Title: 【FrameScript】【React】 */}
            <div style={{
                opacity: subtextProgress,
                transform: `translateY(${(1 - subtextProgress) * 20}px)`,
                marginTop: '20px',
                fontSize: '32px',
                color: '#3b82f6',
                fontWeight: '600',
                zIndex: 10,
                letterSpacing: '4px'
            }}>
                【FrameScript】【React】
            </div>

            {/* Bottom info bar (similar to video) */}
            <div style={{
                position: 'absolute',
                bottom: '40px',
                fontSize: '14px',
                color: '#555',
                fontFamily: 'monospace'
            }}>
                FPS: 30 | Frame: {currentFrame} | Engine: React
            </div>
        </div>
    );
};

export default RecreationScene;
