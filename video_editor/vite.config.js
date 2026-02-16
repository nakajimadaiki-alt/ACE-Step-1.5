import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { mkdirSync, writeFileSync, createReadStream, statSync } from 'node:fs'
import { join, resolve, basename } from 'node:path'
import { spawn } from 'node:child_process'
import { randomUUID } from 'node:crypto'

function apiPlugin() {
  const uploadsDir = resolve('public/uploads')

  return {
    name: 'api-plugin',
    configureServer(server) {
      // Ensure uploads directory exists
      mkdirSync(uploadsDir, { recursive: true })

      server.middlewares.use((req, res, next) => {
        // POST /api/upload
        if (req.method === 'POST' && req.url === '/api/upload') {
          const contentType = req.headers['content-type'] || ''
          const ext = contentType.includes('png') ? '.png'
            : contentType.includes('jpeg') || contentType.includes('jpg') ? '.jpg'
              : contentType.includes('webp') ? '.webp'
                : contentType.includes('gif') ? '.gif'
                  : '.png'

          const filename = `${randomUUID()}${ext}`
          const chunks = []

          req.on('data', (chunk) => chunks.push(chunk))
          req.on('end', () => {
            const buffer = Buffer.concat(chunks)
            writeFileSync(join(uploadsDir, filename), buffer)
            res.writeHead(200, { 'Content-Type': 'application/json' })
            res.end(JSON.stringify({ url: `/uploads/${filename}` }))
          })
          return
        }

        // POST /api/export
        if (req.method === 'POST' && req.url === '/api/export') {
          const chunks = []
          req.on('data', (chunk) => chunks.push(chunk))
          req.on('end', () => {
            let body
            try {
              body = JSON.parse(Buffer.concat(chunks).toString())
            } catch {
              res.writeHead(400, { 'Content-Type': 'application/json' })
              res.end(JSON.stringify({ error: 'Invalid JSON' }))
              return
            }

            const distDir = resolve('dist')
            mkdirSync(distDir, { recursive: true })
            const outFilename = `export_${Date.now()}.mp4`
            const outPath = join(distDir, outFilename)

            const addr = server.httpServer.address()
            const baseUrl = `http://localhost:${addr.port}`

            const scriptArgs = [
              resolve('scripts/export-video.mjs'),
              '--scene', body.scene || 'disc',
              '--image', body.image || '',
              '--disc-style', body.discStyle || 'simple',
              '--duration', String(body.duration || 5),
              '--loop-duration', String(body.loopDuration || 0),
              '--fps', String(body.fps || 30),
              '--out', outPath,
              '--base-url', baseUrl,
            ]

            if (body.imageOffsetX != null) {
              scriptArgs.push('--image-offset-x', String(body.imageOffsetX))
            }
            if (body.imageOffsetY != null) {
              scriptArgs.push('--image-offset-y', String(body.imageOffsetY))
            }
            if (body.imageScale != null) {
              scriptArgs.push('--image-scale', String(body.imageScale))
            }

            res.writeHead(200, {
              'Content-Type': 'application/x-ndjson',
              'Transfer-Encoding': 'chunked',
              'Cache-Control': 'no-cache',
            })

            const proc = spawn(process.execPath, scriptArgs, {
              stdio: ['ignore', 'pipe', 'pipe'],
            })

            const sendLine = (obj) => {
              try { res.write(JSON.stringify(obj) + '\n') } catch { }
            }

            const parseProgress = (text) => {
              // Match "Captured 30/150" pattern
              const m = text.match(/Captured (\d+)\/(\d+)/)
              if (m) {
                console.log(`[Export] Captured ${m[1]}/${m[2]}`)
                sendLine({ type: 'progress', current: Number(m[1]), total: Number(m[2]) })
              }
              // Match stage messages
              if (text.includes('Starting render server')) {
                console.log('[Export] Stage: サーバー起動中...')
                sendLine({ type: 'stage', message: 'サーバー起動中...' })
              }
              if (text.includes('Rendering')) {
                console.log('[Export] Stage: フレームキャプチャ中...')
                sendLine({ type: 'stage', message: 'フレームキャプチャ中...' })
              }
              if (text.includes('Encoding')) {
                console.log('[Export] Stage: エンコード中...')
                sendLine({ type: 'stage', message: 'エンコード中...' })
              }
              if (text.includes('Looping')) {
                console.log('[Export] Stage: ループ処理中...')
                sendLine({ type: 'stage', message: 'ループ処理中...' })
              }
              if (text.includes('Done:')) {
                console.log(`[Export] Done: ${outFilename}`)
                sendLine({ type: 'done', filename: outFilename })
              }
            }

            proc.stdout.on('data', (d) => parseProgress(String(d)))
            proc.stderr.on('data', (d) => parseProgress(String(d)))

            proc.on('close', (code) => {
              if (code === 0) {
                sendLine({ type: 'done', filename: outFilename })
              } else {
                sendLine({ type: 'error', message: `Export failed (exit code ${code})` })
              }
              res.end()
            })

            proc.on('error', (err) => {
              sendLine({ type: 'error', message: err.message })
              res.end()
            })
          })
          return
        }

        // GET /api/export/download/:filename
        if (req.method === 'GET' && req.url?.startsWith('/api/export/download/')) {
          const filename = basename(decodeURIComponent(req.url.replace('/api/export/download/', '')))
          const filePath = join(resolve('dist'), filename)
          try {
            const stat = statSync(filePath)
            res.writeHead(200, {
              'Content-Type': 'video/mp4',
              'Content-Length': stat.size,
              'Content-Disposition': `attachment; filename="${filename}"`,
            })
            createReadStream(filePath).pipe(res)
          } catch {
            res.writeHead(404, { 'Content-Type': 'application/json' })
            res.end(JSON.stringify({ error: 'File not found' }))
          }
          return
        }

        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), apiPlugin()],
})
