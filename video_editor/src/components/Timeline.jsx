import React, { useRef } from 'react';
import { FPS } from '../constants';
import '../styles/Timeline.css';

const Timeline = ({ currentFrame, duration, isPlaying, onTogglePlayback, onSeek }) => {
    const scrollRef = useRef(null);
    const zoom = 2; // pixels per frame

    const handleTimelineClick = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left + e.currentTarget.scrollLeft;
        const frame = Math.floor(x / zoom);
        onSeek(frame);
    };

    const framesArr = Array.from({ length: duration + 1 });

    return (
        <div className="timeline-container">
            <div className="timeline-toolbar">
                <div className="playback-controls">
                    <button onClick={onTogglePlayback} className="play-button">
                        {isPlaying ? '停止' : '再生'}
                    </button>
                    <div className="time-display">
                        {Math.floor(currentFrame / FPS)}秒 / {Math.floor(duration / FPS)}秒
                        <span className="frame-count">{currentFrame}f</span>
                    </div>
                </div>
            </div>

            <div className="scroll-container" ref={scrollRef}>
                <div
                    className="timeline-tracks"
                    onClick={handleTimelineClick}
                    style={{ width: duration * zoom + 100 }}
                >
                    <div className="timeline-ruler">
                        {framesArr.map((_, i) => (
                            i % 10 === 0 ? (
                                <div
                                    key={i}
                                    className="ruler-tick major"
                                    style={{ left: i * zoom }}
                                >
                                    <span className="tick-label">{i}f</span>
                                </div>
                            ) : null
                        ))}
                    </div>

                    <div
                        className="playhead"
                        style={{ transform: `translateX(${currentFrame * zoom}px)` }}
                    />
                </div>
            </div>
        </div>
    );
};

export default Timeline;
