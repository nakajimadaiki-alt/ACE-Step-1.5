import React, { useEffect, useState, useRef } from 'react';
import Preview from './Preview';
import Timeline from './Timeline';
import ExampleScene from './ExampleScene';
import AutoScene from './AutoScene';
import RecreationScene from './RecreationScene';
import StaticImageScene from './StaticImageScene';
import DiscScene from './DiscScene';
import Sidebar from './Sidebar';
import Inspector from './Inspector';
import { useVideoEngine } from '../hooks/useVideoEngine';
import '../styles/Editor.css';

const Editor = () => {
    const {
        currentFrame,
        isPlaying,
        duration,
        togglePlayback,
        seek,
        setDuration
    } = useVideoEngine();

    const [activeScene, setActiveScene] = useState('static'); // 'static', 'recreation', 'example', 'auto', 'disc'
    const [staticImageSrc, setStaticImageSrc] = useState('');
    const [uploadedImageSrc, setUploadedImageSrc] = useState('');
    const [script, setScript] = useState([
        { text: 'AIが自動演出', effect: 'fade' },
        { text: '文字を並べるだけ', effect: 'slide' },
        { text: '爆速動画制作', effect: 'bounce' },
    ]);
    const [inputText, setInputText] = useState('');
    const [discStyle, setDiscStyle] = useState('simple'); // 'simple' | 'vinyl'

    // Image position adjustment
    const [imageOffsetX, setImageOffsetX] = useState(50);
    const [imageOffsetY, setImageOffsetY] = useState(50);
    const [imageScale, setImageScale] = useState(1.0);

    // Export state
    const [exportState, setExportState] = useState('idle'); // 'idle' | 'exporting' | 'done' | 'error'
    const [rotationPeriod, setRotationPeriod] = useState(10); // seconds per revolution
    const [exportDuration, setExportDuration] = useState(30); // Total duration (seconds)
    const [exportProgress, setExportProgress] = useState(0);
    const [exportStage, setExportStage] = useState('');
    const [exportFilename, setExportFilename] = useState('');
    const [exportError, setExportError] = useState('');
    const abortRef = useRef(null);

    const addScriptItem = () => {
        if (!inputText) return;
        const effects = ['fade', 'slide', 'bounce'];
        const randomEffect = effects[Math.floor(Math.random() * effects.length)];
        const newScript = [...script, { text: inputText, effect: randomEffect }];
        setScript(newScript);
        setDuration(newScript.length * 60);
        setInputText('');
    };

    const handleStaticImageFileChange = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Content-Type': file.type },
                body: file,
            });
            const data = await res.json();
            setUploadedImageSrc(data.url);
        } catch {
            // Fallback to blob URL if upload fails
            const objectUrl = URL.createObjectURL(file);
            setUploadedImageSrc(objectUrl);
        }
    };

    const handleExport = async () => {
        setExportState('exporting');
        setExportProgress(0);
        setExportStage('開始中...');
        setExportFilename('');
        setExportError('');

        const controller = new AbortController();
        abortRef.current = controller;

        try {
            const res = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scene: activeScene,
                    image: uploadedImageSrc || staticImageSrc,
                    discStyle,
                    duration: activeScene === 'disc' ? rotationPeriod : exportDuration,
                    loopDuration: activeScene === 'disc' ? exportDuration : 0,
                    imageOffsetX,
                    imageOffsetY,
                    imageScale,
                }),
                signal: controller.signal,
            });

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const msg = JSON.parse(line);
                        if (msg.type === 'progress') {
                            setExportProgress(Math.round((msg.current / msg.total) * 100));
                        } else if (msg.type === 'stage') {
                            setExportStage(msg.message);
                        } else if (msg.type === 'done') {
                            setExportFilename(msg.filename);
                            setExportState('done');
                            setExportProgress(100);
                            setExportStage('完了');
                        } else if (msg.type === 'error') {
                            setExportError(msg.message);
                            setExportState('error');
                        }
                    } catch { /* ignore parse errors */ }
                }
            }
        } catch (err) {
            if (err.name !== 'AbortError') {
                setExportError(err.message);
                setExportState('error');
            }
        }
    };

    const handleDownload = () => {
        if (!exportFilename) return;
        const a = document.createElement('a');
        a.href = `/api/export/download/${encodeURIComponent(exportFilename)}`;
        a.download = exportFilename;
        a.click();
    };

    const imageSrc = uploadedImageSrc || staticImageSrc;

    return (
        <div className="editor-container">
            {/* Left Sidebar */}
            <Sidebar activeScene={activeScene} setActiveScene={setActiveScene} />

            {/* Center: Preview & Timeline */}
            <div className="center-area">
                <main className="preview-area">
                    <div className="canvas-wrapper">
                        <Preview currentFrame={currentFrame}>
                            {activeScene === 'static' ? (
                                <StaticImageScene imageSrc={imageSrc} />
                            ) : activeScene === 'recreation' ? (
                                <RecreationScene currentFrame={currentFrame} />
                            ) : activeScene === 'auto' ? (
                                <AutoScene currentFrame={currentFrame} script={script} />
                            ) : activeScene === 'example' ? (
                                <ExampleScene currentFrame={currentFrame} />
                            ) : activeScene === 'disc' ? (
                                <DiscScene
                                    currentFrame={currentFrame}
                                    imageSrc={imageSrc}
                                    discStyle={discStyle}
                                    imageOffsetX={imageOffsetX}
                                    imageOffsetY={imageOffsetY}
                                    imageScale={imageScale}
                                    rotationPeriod={rotationPeriod}
                                />
                            ) : null}
                        </Preview>
                    </div>
                </main>
                <div className="timeline-area">
                    <Timeline
                        currentFrame={currentFrame}
                        duration={duration}
                        isPlaying={isPlaying}
                        onTogglePlayback={togglePlayback}
                        onSeek={seek}
                    />
                </div>
            </div>

            {/* Right: Inspector */}
            <Inspector
                activeScene={activeScene}
                imageSrc={imageSrc}
                staticImageSrc={staticImageSrc}
                setStaticImageSrc={setStaticImageSrc}
                handleStaticImageFileChange={handleStaticImageFileChange}
                discStyle={discStyle}
                setDiscStyle={setDiscStyle}
                imageOffsetX={imageOffsetX}
                setImageOffsetX={setImageOffsetX}
                imageOffsetY={imageOffsetY}
                setImageOffsetY={setImageOffsetY}
                imageScale={imageScale}
                setImageScale={setImageScale}
                rotationPeriod={rotationPeriod}
                setRotationPeriod={setRotationPeriod}
                exportDuration={exportDuration}
                setExportDuration={setExportDuration}
                exportState={exportState}
                exportProgress={exportProgress}
                exportStage={exportStage}
                exportFilename={exportFilename}
                exportError={exportError}
                handleExport={handleExport}
                handleDownload={handleDownload}
                inputText={inputText}
                setInputText={setInputText}
                script={script}
                addScriptItem={addScriptItem}
            />
        </div>
    );
};

export default Editor;
