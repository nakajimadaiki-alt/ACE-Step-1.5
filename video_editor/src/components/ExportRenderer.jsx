import React, { useState, useEffect } from 'react';
import ExampleScene from './ExampleScene';
import AutoScene from './AutoScene';
import RecreationScene from './RecreationScene';
import StaticImageScene from './StaticImageScene';
import DiscScene from './DiscScene';

const defaultScript = [
    { text: 'AIが自動演出', effect: 'fade' },
    { text: '文字を並べるだけ', effect: 'slide' },
    { text: '爆速動画制作', effect: 'bounce' },
];

const parseNumber = (value, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
};

const ExportRenderer = () => {
    const params = new URLSearchParams(window.location.search);
    const scene = params.get('scene') || 'static';
    const image = params.get('image') || '';
    const discStyle = params.get('discStyle') || 'simple';
    const imageOffsetX = parseNumber(params.get('imageOffsetX'), 50);
    const imageOffsetY = parseNumber(params.get('imageOffsetY'), 50);
    const imageScale = parseNumber(params.get('imageScale'), 1);
    const initialFrame = Math.max(0, Math.floor(parseNumber(params.get('frame'), 0)));

    const [frame, setFrame] = useState(initialFrame);

    useEffect(() => {
        // Expose a global function so Playwright can update the frame
        // without a full page navigation per frame.
        window.__setExportFrame = (f) => {
            setFrame(f);
            return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        };
        window.__exportReady = true;
        return () => {
            delete window.__setExportFrame;
            delete window.__exportReady;
        };
    }, []);

    let content = null;
    if (scene === 'disc') {
        content = (
            <DiscScene
                currentFrame={frame}
                imageSrc={image}
                discStyle={discStyle}
                imageOffsetX={imageOffsetX}
                imageOffsetY={imageOffsetY}
                imageScale={imageScale}
            />
        );
    } else if (scene === 'recreation') {
        content = <RecreationScene currentFrame={frame} />;
    } else if (scene === 'auto') {
        content = <AutoScene currentFrame={frame} script={defaultScript} />;
    } else if (scene === 'example') {
        content = <ExampleScene currentFrame={frame} />;
    } else {
        content = <StaticImageScene imageSrc={image} />;
    }

    return (
        <div
            style={{
                margin: 0,
                padding: 0,
                width: '100vw',
                height: '100vh',
                background: '#000',
                overflow: 'hidden',
            }}
        >
            <div
                id="export-canvas"
                style={{
                    width: '100%',
                    height: '100%',
                    position: 'relative',
                    overflow: 'hidden',
                }}
            >
                {content}
            </div>
        </div>
    );
};

export default ExportRenderer;
