# how to view RTSP in browser

1. RTSP → HLS

```
ffmpeg -i rtsp://your_camera_url \
       -c:v copy -c:a aac \
       -f hls \
       -hls_time 2 \
       -hls_list_size 5 \
       -hls_flags delete_segments \
       /path/to/webroot/stream.m3u8
```

2. RTSP → WebRTC

`ffmpeg -i rtsp://... -f rtp ...`

3. RTSP → MJPEG

`ffmpeg -i rtsp://your_camera_url -f mjpeg -q 5 http://localhost:8090/feed`

4. RTSP → MP4 Fragments

Demo in this repo
