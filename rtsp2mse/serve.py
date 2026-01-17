#!/usr/bin/env python3
import sys
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

RTSP_URL = sys.argv[1] if len(sys.argv) > 1 else None
if not RTSP_URL:
    print("Usage: python server.py rtsp://USER:PASS@HOST/stream")
    sys.exit(1)

HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>RTSP via MSE</title>
</head>
<body>
<h3>RTSP → FFmpeg → MSE</h3>
<video id="v" autoplay muted playsinline controls></video>

<script>
const video = document.getElementById("v");
const ms = new MediaSource();
video.src = URL.createObjectURL(ms);

ms.addEventListener("sourceopen", async () => {
  const sb = ms.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');

  const res = await fetch("/stream");
  const reader = res.body.getReader();

  async function pump() {
    const { done, value } = await reader.read();
    if (done) return;
    if (!sb.updating) sb.appendBuffer(value);
    sb.addEventListener("updateend", pump, { once: true });
  }

  pump();
});
</script>
</body>
</html>
""".encode()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML)))
            self.end_headers()
            self.wfile.write(HTML)
            return

        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            ffmpeg = subprocess.Popen(
                [
                    "ffmpeg",
                    "-rtsp_transport", "tcp",
                    "-i", RTSP_URL,
                    "-an",
                    "-c:v", "copy",
                    "-movflags", "frag_keyframe+empty_moov",
                    "-f", "mp4",
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                bufsize=0,
            )

            try:
                while True:
                    data = ffmpeg.stdout.read(4096)
                    if not data:
                        break
                    self.wfile.write(data)
            except BrokenPipeError:
                # print('shit')
                pass
            finally:
                ffmpeg.kill()
            return

        self.send_error(404)

def main():
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("Open http://127.0.0.1:8080/")
    server.serve_forever()

if __name__ == "__main__":
    main()
