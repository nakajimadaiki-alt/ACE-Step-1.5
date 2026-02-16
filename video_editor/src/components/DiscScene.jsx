import React, { useState } from 'react';
import { FPS, DISC_ROTATION_SECONDS } from '../constants';

const DiscScene = ({ currentFrame, imageSrc, discStyle = 'simple', imageOffsetX = 50, imageOffsetY = 50, imageScale = 1, rotationPeriod = 10 }) => {
    const [imgError, setImgError] = useState('');
    const loadError = !!imageSrc && imgError === imageSrc;

    const rotation = (currentFrame / (FPS * rotationPeriod)) * 360;

    if (!imageSrc || loadError) {
        return (
            <div style={{
                width: '100%', height: '100%', background: '#000',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#cbd5e1', fontSize: '18px',
            }}>
                画像を選択してください
            </div>
        );
    }

    const imageProps = { imageOffsetX, imageOffsetY, imageScale };

    if (discStyle === 'vinyl') {
        return <VinylDisc rotation={rotation} imageSrc={imageSrc} onError={() => setImgError(imageSrc)} onLoad={() => setImgError('')} {...imageProps} />;
    }

    return <SimpleDisc rotation={rotation} imageSrc={imageSrc} onError={() => setImgError(imageSrc)} onLoad={() => setImgError('')} {...imageProps} />;
};

const SimpleDisc = ({ rotation, imageSrc, onError, onLoad, imageOffsetX, imageOffsetY, imageScale }) => {
    const size = '85vh';
    return (
        <div style={{
            width: '100%', height: '100%', background: '#000',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                width: size, height: size, maxWidth: '50vw', maxHeight: '50vw',
                borderRadius: '50%', overflow: 'hidden',
                transform: `rotate(${rotation}deg)`,
                boxShadow: '0 0 60px rgba(0,0,0,0.8), 0 0 120px rgba(0,0,0,0.4)',
            }}>
                <img
                    key={imageSrc}
                    src={imageSrc}
                    alt="disc"
                    onError={onError}
                    onLoad={onLoad}
                    style={{
                        width: '100%', height: '100%', objectFit: 'cover',
                        display: 'block',
                        objectPosition: `${imageOffsetX}% ${imageOffsetY}%`,
                        transform: `scale(${imageScale})`,
                    }}
                />
            </div>
        </div>
    );
};

const VinylDisc = ({ rotation, imageSrc, onError, onLoad, imageOffsetX, imageOffsetY, imageScale }) => {
    const size = '85vh';
    return (
        <div style={{
            width: '100%', height: '100%', background: '#000',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                width: size, height: size, maxWidth: '50vw', maxHeight: '50vw',
                borderRadius: '50%', position: 'relative',
                transform: `rotate(${rotation}deg)`,
                boxShadow: '0 0 60px rgba(0,0,0,0.8), 0 0 120px rgba(0,0,0,0.4)',
                background: '#111',
            }}>
                {/* Vinyl grooves */}
                <div style={{
                    position: 'absolute', inset: 0, borderRadius: '50%',
                    background: `
                        repeating-radial-gradient(
                            circle at center,
                            transparent 0px,
                            transparent 3px,
                            rgba(40,40,40,0.6) 3px,
                            rgba(40,40,40,0.6) 4px
                        )
                    `,
                    zIndex: 1,
                }} />

                {/* Outer rim highlight */}
                <div style={{
                    position: 'absolute', inset: 0, borderRadius: '50%',
                    border: '3px solid rgba(60,60,60,0.5)',
                    zIndex: 2,
                }} />

                {/* Center label (image) */}
                <div style={{
                    position: 'absolute',
                    top: '50%', left: '50%',
                    width: '38%', height: '38%',
                    transform: 'translate(-50%, -50%)',
                    borderRadius: '50%', overflow: 'hidden',
                    zIndex: 3,
                    border: '2px solid rgba(80,80,80,0.5)',
                }}>
                    <img
                        key={imageSrc}
                        src={imageSrc}
                        alt="disc label"
                        onError={onError}
                        onLoad={onLoad}
                        style={{
                            width: '100%', height: '100%',
                            objectFit: 'cover', display: 'block',
                            objectPosition: `${imageOffsetX}% ${imageOffsetY}%`,
                            transform: `scale(${imageScale})`,
                        }}
                    />
                </div>

                {/* Spindle hole */}
                <div style={{
                    position: 'absolute',
                    top: '50%', left: '50%',
                    width: '12px', height: '12px',
                    transform: 'translate(-50%, -50%)',
                    borderRadius: '50%',
                    background: '#222',
                    border: '2px solid #444',
                    zIndex: 4,
                }} />

                {/* Subtle light reflection */}
                <div style={{
                    position: 'absolute', inset: 0, borderRadius: '50%',
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 50%, rgba(255,255,255,0.01) 100%)',
                    zIndex: 5,
                }} />
            </div>
        </div>
    );
};

export default DiscScene;
