import React from 'react';

const AutoScene = ({ currentFrame, script }) => {
    if (!script || script.length === 0) return null;

    const FPS = 30;
    const durationPerItem = 60; // 2 seconds per text
    const totalDuration = script.length * durationPerItem;

    const currentIndex = Math.floor((currentFrame % totalDuration) / durationPerItem);
    const itemProgress = (currentFrame % durationPerItem) / durationPerItem;
    const item = script[currentIndex];

    // Animation variants
    const getStyle = (type, progress) => {
        switch (type) {
            case 'fade':
                return {
                    opacity: progress < 0.2 ? progress * 5 : progress > 0.8 ? (1 - progress) * 5 : 1,
                    transform: `scale(${0.9 + progress * 0.2})`,
                };
            case 'slide':
                return {
                    opacity: progress < 0.1 ? progress * 10 : progress > 0.9 ? (1 - progress) * 10 : 1,
                    transform: `translateX(${(0.5 - progress) * 100}px)`,
                };
            case 'bounce':
                return {
                    transform: `translateY(${Math.sin(progress * Math.PI) * -50}px) scale(${1 + Math.sin(progress * Math.PI * 2) * 0.1})`,
                };
            default:
                return { opacity: 1 };
        }
    };

    return (
        <div style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'radial-gradient(circle, #1a1a1a 0%, #050505 100%)',
            color: 'white'
        }}>
            <div style={{
                textAlign: 'center',
                fontSize: '56px',
                fontWeight: '900',
                textShadow: '0 10px 20px rgba(0,0,0,0.5)',
                ...getStyle(item.effect, itemProgress)
            }}>
                {item.text}
            </div>

            {/* Visual background effect */}
            <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                border: '20px solid rgba(59, 130, 246, 0.1)',
                boxSizing: 'border-box',
                pointerEvents: 'none',
                transform: `scale(${1 + itemProgress * 0.05})`,
            }} />
        </div>
    );
};

export default AutoScene;
