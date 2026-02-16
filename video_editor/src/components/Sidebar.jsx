import React from 'react';

const Sidebar = ({ activeScene, setActiveScene }) => {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <span className="logo-icon">🎬</span>
                <span className="logo-text">VideoMaker</span>
            </div>
            <nav className="scene-list">
                <button
                    className={`scene-item ${activeScene === 'static' ? 'active' : ''}`}
                    onClick={() => setActiveScene('static')}
                >
                    <span className="icon">🖼</span>
                    <span className="label">静止画表示</span>
                </button>
                <button
                    className={`scene-item ${activeScene === 'disc' ? 'active' : ''}`}
                    onClick={() => setActiveScene('disc')}
                >
                    <span className="icon">💿</span>
                    <span className="label">円盤回転</span>
                </button>
                <button
                    className={`scene-item ${activeScene === 'recreation' ? 'active' : ''}`}
                    onClick={() => setActiveScene('recreation')}
                >
                    <span className="icon">🎬</span>
                    <span className="label">再現テンプレ</span>
                </button>
                <button
                    className={`scene-item ${activeScene === 'auto' ? 'active' : ''}`}
                    onClick={() => setActiveScene('auto')}
                >
                    <span className="icon">✨</span>
                    <span className="label">自動演出</span>
                </button>
                <button
                    className={`scene-item ${activeScene === 'example' ? 'active' : ''}`}
                    onClick={() => setActiveScene('example')}
                >
                    <span className="icon">📦</span>
                    <span className="label">モーション</span>
                </button>
            </nav>
        </aside>
    );
};

export default Sidebar;
