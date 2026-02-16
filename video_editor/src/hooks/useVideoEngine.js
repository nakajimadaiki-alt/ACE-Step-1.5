import { useState, useEffect, useRef, useCallback } from 'react';
import { FPS, DEFAULT_DURATION_FRAMES } from '../constants';

export const useVideoEngine = () => {
    const [currentFrame, setCurrentFrame] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [duration, setDuration] = useState(DEFAULT_DURATION_FRAMES);
    const requestRef = useRef();
    const startTimeRef = useRef();

    const play = useCallback(() => {
        setIsPlaying(true);
        startTimeRef.current = performance.now() - (currentFrame / FPS) * 1000;
    }, [currentFrame]);

    const pause = useCallback(() => {
        setIsPlaying(false);
        if (requestRef.current) {
            cancelAnimationFrame(requestRef.current);
        }
    }, []);

    const seek = useCallback((frame) => {
        const targetFrame = Math.max(0, Math.min(frame, duration));
        setCurrentFrame(targetFrame);
        if (isPlaying) {
            startTimeRef.current = performance.now() - (targetFrame / FPS) * 1000;
        }
    }, [duration, isPlaying]);

    const togglePlayback = useCallback(() => {
        if (isPlaying) pause();
        else play();
    }, [isPlaying, pause, play]);

    useEffect(() => {
        const animate = (time) => {
            if (isPlaying) {
                const elapsed = time - startTimeRef.current;
                const nextFrame = Math.floor((elapsed / 1000) * FPS);

                if (nextFrame >= duration) {
                    setCurrentFrame(duration);
                    setIsPlaying(false);
                } else {
                    setCurrentFrame(nextFrame);
                    requestRef.current = requestAnimationFrame(animate);
                }
            }
        };

        if (isPlaying) {
            requestRef.current = requestAnimationFrame(animate);
        }

        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, [isPlaying, duration]);

    return {
        currentFrame,
        isPlaying,
        duration,
        play,
        pause,
        seek,
        togglePlayback,
        setCurrentFrame,
        setDuration,
    };
};
