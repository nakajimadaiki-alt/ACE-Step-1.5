import { spawn } from 'node:child_process';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import http from 'node:http';

const args = process.argv.slice(2);

const readArg = (name, fallback) => {
    const idx = args.indexOf(`--${name}`);
    if (idx === -1) return fallback;
    return args[idx + 1] ?? fallback;
};

const parseNum = (value, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
};

const scene = readArg('scene', 'static');
const image = readArg('image', '');
const discStyle = readArg('disc-style', 'simple');
const fps = parseNum(readArg('fps', '30'), 30);
const durationSec = parseNum(readArg('duration', '5'), 5);
const loopDuration = parseNum(readArg('loop-duration', '0'), 0);
const width = parseNum(readArg('width', '1920'), 1920);
const height = parseNum(readArg('height', '1080'), 1080);
const out = resolve(readArg('out', './dist/export.mp4'));
const port = parseNum(readArg('port', '4173'), 4173);
const baseUrlArg = readArg('base-url', '');
const imageOffsetX = parseNum(readArg('image-offset-x', '50'), 50);
const imageOffsetY = parseNum(readArg('image-offset-y', '50'), 50);
const imageScale = parseNum(readArg('image-scale', '1'), 1);
const totalFrames = Math.max(1, Math.floor(fps * durationSec));

const run = (cmd, cmdArgs, opts = {}) =>
    new Promise((resolvePromise, rejectPromise) => {
        const proc = spawn(cmd, cmdArgs, { stdio: 'pipe', shell: process.platform === 'win32', ...opts });
        let stderr = '';

        if (proc.stderr) {
            proc.stderr.on('data', (d) => {
                stderr += String(d);
            });
        }

        proc.on('error', rejectPromise);
        proc.on('close', (code) => {
            if (code === 0) resolvePromise({ stderr });
            else rejectPromise(new Error(stderr || `${cmd} failed with exit code ${code}`));
        });
    });

const waitForServer = (url, timeoutMs = 30000) =>
    new Promise((resolvePromise, rejectPromise) => {
        const start = Date.now();
        const attempt = () => {
            const req = http.get(url, (res) => {
                res.resume();
                if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
                    resolvePromise();
                } else if (Date.now() - start > timeoutMs) {
                    rejectPromise(new Error(`Server did not start in time: ${url}`));
                } else {
                    setTimeout(attempt, 500);
                }
            });
            req.on('error', () => {
                if (Date.now() - start > timeoutMs) {
                    rejectPromise(new Error(`Server did not start in time: ${url}`));
                } else {
                    setTimeout(attempt, 500);
                }
            });
        };
        attempt();
    });

const printUsage = () => {
    console.log('Usage: npm run export -- --scene static --image /static-image.jpg --duration 10 --fps 30 --out ./dist/video.mp4');
    console.log('Scenes: static, recreation, auto, example, disc');
    console.log('');
    console.log('Disc options:');
    console.log('  --disc-style simple|vinyl');
    console.log('  --image-offset-x <0-100>    Image X offset percentage (default: 50)');
    console.log('  --image-offset-y <0-100>    Image Y offset percentage (default: 50)');
    console.log('  --image-scale <1.0-3.0>     Image scale factor (default: 1)');
    console.log('  --loop-duration <seconds>   Loop the rendered clip to this total length (e.g. 3600 for 1h)');
    console.log('  --base-url <url>            Use existing dev server instead of starting a new one');
};

const startViteServer = (portNumber) => {
    const proc = spawn(
        process.platform === 'win32' ? 'npm.cmd' : 'npm',
        ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(portNumber), '--strictPort'],
        { stdio: ['ignore', 'pipe', 'pipe'], shell: process.platform === 'win32' },
    );

    proc.stdout?.pipe(process.stdout);
    proc.stderr?.pipe(process.stderr);
    return proc;
};

const frameName = (index) => `frame_${String(index).padStart(6, '0')}.png`;

const captureFrames = async (framesDir, baseUrl, frameCount) => {
    let chromium;
    try {
        ({ chromium } = await import('playwright'));
    } catch {
        throw new Error('Missing dependency: playwright. Run `npm i -D playwright` first.');
    }

    const browser = await chromium.launch({ headless: true });

    try {
        const page = await browser.newPage({ viewport: { width, height } });

        // Load the export page once, then update frames via JS to avoid
        // per-frame page navigation overhead.
        const qs = new URLSearchParams({
            scene,
            frame: '0',
            image,
            discStyle,
            imageOffsetX: String(imageOffsetX),
            imageOffsetY: String(imageOffsetY),
            imageScale: String(imageScale),
        });
        await page.goto(`${baseUrl}/export?${qs.toString()}`, { waitUntil: 'load' });
        await page.waitForFunction(() => window.__exportReady === true, null, { timeout: 10000 });

        const canvas = page.locator('#export-canvas');
        const logInterval = Math.max(1, Math.floor(frameCount / 20));

        for (let i = 0; i < frameCount; i += 1) {
            await page.evaluate((f) => window.__setExportFrame(f), i);
            const outPath = join(framesDir, frameName(i));
            const buffer = await canvas.screenshot({ type: 'png' });
            await writeFile(outPath, buffer);
            if (i % logInterval === 0) {
                console.log(`Captured ${i}/${frameCount}`);
            }
        }
    } finally {
        await browser.close();
    }
};

const encodeVideo = async (framesDir, outputPath) => {
    await run('ffmpeg', [
        '-y',
        '-framerate',
        String(fps),
        '-i',
        join(framesDir, 'frame_%06d.png'),
        '-c:v',
        'libx264',
        '-pix_fmt',
        'yuv420p',
        '-crf',
        '18',
        '-movflags',
        '+faststart',
        outputPath,
    ]);
};

const loopVideo = async (inputPath, outputPath, totalSeconds) => {
    const loopCount = Math.ceil(totalSeconds / durationSec);
    await run('ffmpeg', [
        '-y',
        '-stream_loop',
        String(loopCount),
        '-i',
        inputPath,
        '-c',
        'copy',
        '-t',
        String(totalSeconds),
        outputPath,
    ]);
};

const main = async () => {
    if (!['static', 'recreation', 'auto', 'example', 'disc'].includes(scene)) {
        printUsage();
        throw new Error(`Invalid --scene: ${scene}`);
    }

    await run('ffmpeg', ['-version']).catch(() => {
        throw new Error('ffmpeg is not installed or not in PATH.');
    });

    const framesDir = await mkdtemp(join(tmpdir(), 'video-editor-export-'));
    let viteProc = null;
    let baseUrl;

    if (baseUrlArg) {
        // Use the existing server provided by --base-url
        baseUrl = baseUrlArg;
    } else {
        viteProc = startViteServer(port);
        baseUrl = `http://127.0.0.1:${port}`;
    }

    try {
        if (!baseUrlArg) {
            console.log('Starting render server...');
            await waitForServer(baseUrl);
        }
        console.log(`Rendering ${totalFrames} frames (${fps}fps x ${durationSec}s)...`);
        await captureFrames(framesDir, baseUrl, totalFrames);

        if (loopDuration > 0) {
            const loopSrc = join(framesDir, '_loop_src.mp4');
            console.log('Encoding single loop MP4...');
            await encodeVideo(framesDir, loopSrc);
            console.log(`Looping to ${loopDuration}s with ffmpeg...`);
            await loopVideo(loopSrc, out, loopDuration);
        } else {
            console.log('Encoding MP4 with ffmpeg...');
            await encodeVideo(framesDir, out);
        }

        console.log(`Done: ${out}`);
    } finally {
        if (viteProc) viteProc.kill();
        await rm(framesDir, { recursive: true, force: true });
    }
};

main().catch((err) => {
    console.error(err.message);
    process.exit(1);
});
