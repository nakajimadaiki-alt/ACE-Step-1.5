import React, { useState } from 'react';

const StaticImageScene = ({ imageSrc }) => {
    const [errorSrc, setErrorSrc] = useState('');
    const loadError = !!imageSrc && errorSrc === imageSrc;

    if (!imageSrc || loadError) {
        return (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    background: '#000',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#cbd5e1',
                    fontSize: '18px'
                }}
            >
                画像を読み込めません。ファイル選択か有効なURL/`public`配下パスを指定してください。
            </div>
        );
    }

    return (
        <div
            style={{
                width: '100%',
                height: '100%',
                background: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden'
            }}
        >
            <img
                key={imageSrc}
                src={imageSrc}
                alt="Static scene"
                onError={() => setErrorSrc(imageSrc)}
                onLoad={() => setErrorSrc('')}
                style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain'
                }}
            />
        </div>
    );
};

export default StaticImageScene;
