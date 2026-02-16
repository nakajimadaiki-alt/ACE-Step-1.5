import React from 'react';

const Inspector = ({
    activeScene,
    imageSrc,
    staticImageSrc,
    setStaticImageSrc,
    handleStaticImageFileChange,

    // Disc Settings
    discStyle,
    setDiscStyle,
    imageOffsetX,
    setImageOffsetX,
    imageOffsetY,
    setImageOffsetY,
    imageScale,
    setImageScale,
    rotationPeriod,
    setRotationPeriod,
    exportDuration,
    setExportDuration,
    exportState,
    exportProgress,
    exportStage,
    exportFilename,
    exportError,
    handleExport,
    handleDownload,

    // Auto Scene Settings
    inputText,
    setInputText,
    script,
    addScriptItem
}) => {
    return (
        <aside className="inspector">
            {activeScene === 'disc' && (
                <div className="properties-panel">
                    <h3>円盤設定</h3>

                    <details className="settings-group" open>
                        <summary>1. 画像とスタイル</summary>
                        <div className="group-content">
                            <div className="file-dropzone" onClick={() => document.getElementById('file-upload').click()}>
                                {imageSrc ? '画像変更' : 'クリックして画像を選択'}
                                <input
                                    id="file-upload"
                                    type="file"
                                    accept="image/*"
                                    onChange={handleStaticImageFileChange}
                                    style={{ display: 'none' }}
                                />
                            </div>
                            <div className="script-input-group" style={{ marginTop: '10px' }}>
                                <input
                                    type="text"
                                    value={staticImageSrc}
                                    onChange={(e) => setStaticImageSrc(e.target.value)}
                                    placeholder="WEB画像のURLを入力..."
                                />
                            </div>
                            <div className="style-selector" style={{ marginTop: '15px' }}>
                                <button
                                    className={`style-card ${discStyle === 'simple' ? 'active' : ''}`}
                                    onClick={() => setDiscStyle('simple')}
                                >
                                    <div className="card-icon" style={{ borderRadius: '50%', background: '#555' }}></div>
                                    <span>シンプル</span>
                                </button>
                                <button
                                    className={`style-card ${discStyle === 'vinyl' ? 'active' : ''}`}
                                    onClick={() => setDiscStyle('vinyl')}
                                >
                                    <div className="card-icon" style={{ borderRadius: '50%', border: '2px solid #555' }}></div>
                                    <span>レコード</span>
                                </button>
                            </div>
                        </div>
                    </details>

                    <details className="settings-group" open>
                        <summary>2. 位置・サイズ調整</summary>
                        <div className="group-content">
                            <div className="control-row">
                                <label>X位置 ({imageOffsetX}%)</label>
                                <input
                                    type="range"
                                    min="0" max="100"
                                    value={imageOffsetX}
                                    onChange={(e) => setImageOffsetX(Number(e.target.value))}
                                />
                            </div>
                            <div className="control-row">
                                <label>Y位置 ({imageOffsetY}%)</label>
                                <input
                                    type="range"
                                    min="0" max="100"
                                    value={imageOffsetY}
                                    onChange={(e) => setImageOffsetY(Number(e.target.value))}
                                />
                            </div>
                            <div className="control-row">
                                <label>ズーム ({imageScale.toFixed(1)}x)</label>
                                <input
                                    type="range"
                                    min="1.0" max="3.0" step="0.1"
                                    value={imageScale}
                                    onChange={(e) => setImageScale(Number(e.target.value))}
                                />
                            </div>
                        </div>
                    </details>

                    <details className="settings-group" open>
                        <summary>エクスポート設定</summary>
                        <div className="group-content">
                            <div className="control-row">
                                <label>回転速度 ({rotationPeriod}秒/周)</label>
                                <input
                                    type="range"
                                    min="1" max="60"
                                    value={rotationPeriod}
                                    onChange={(e) => setRotationPeriod(Number(e.target.value))}
                                />
                            </div>
                            <div className="control-row">
                                <label>合計時間 ({exportDuration}秒)</label>
                                <input
                                    type="range"
                                    min="5" max="3600" step="5"
                                    value={exportDuration}
                                    onChange={(e) => setExportDuration(Number(e.target.value))}
                                />
                            </div>
                            <button
                                className="export-button"
                                onClick={handleExport}
                                disabled={exportState === 'exporting' || !imageSrc}
                            >
                                {exportState === 'exporting' ? '書き出し中...' : 'MP4書き出し'}
                            </button>

                            {exportState === 'exporting' && (
                                <div className="export-status">
                                    <div className="progress-bar">
                                        <div className="fill" style={{ width: `${exportProgress}%` }}></div>
                                    </div>
                                    <span>{exportStage}</span>
                                </div>
                            )}

                            {exportState === 'done' && (
                                <button className="download-button" onClick={handleDownload}>
                                    ダウンロード
                                </button>
                            )}

                            {exportState === 'error' && (
                                <div className="export-status" style={{ color: 'var(--danger)' }}>
                                    {exportError}
                                </div>
                            )}
                        </div>
                    </details>
                </div>
            )}

            {activeScene === 'static' && (
                <div className="properties-panel">
                    <h3>静止画設定</h3>
                    <div className="group-content">
                        <div className="file-dropzone" onClick={() => document.getElementById('file-upload-static').click()}>
                            {imageSrc ? '画像変更' : 'クリックして画像を選択'}
                            <input
                                id="file-upload-static"
                                type="file"
                                accept="image/*"
                                onChange={handleStaticImageFileChange}
                                style={{ display: 'none' }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {activeScene === 'auto' && (
                <div className="properties-panel">
                    <h3>自動演出設定</h3>
                    <div className="group-content">
                        <div className="input-row">
                            <input
                                type="text"
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder="テロップを入力..."
                                onKeyDown={(e) => e.key === 'Enter' && addScriptItem()}
                            />
                            <button className="export-button" style={{ marginTop: '10px' }} onClick={addScriptItem}>追加</button>
                        </div>
                        <div className="script-list" style={{ marginTop: '20px' }}>
                            {script.map((item, i) => (
                                <div key={i} className="control-row" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-sub)' }}>{i + 1}.</span>
                                    <span style={{ flex: 1 }}>{item.text}</span>
                                    <span style={{ fontSize: '0.8rem', background: '#333', padding: '2px 6px', borderRadius: '4px' }}>{item.effect}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {(activeScene === 'recreation' || activeScene === 'example') && (
                <div className="properties-panel">
                    <h3>設定</h3>
                    <p className="description">このシーンには設定項目はありません。</p>
                </div>
            )}
        </aside>
    );
};

export default Inspector;
