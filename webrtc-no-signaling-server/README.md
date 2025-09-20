webrtc peer to peer chat without signaling server
-------------------------------------------------

https://github.com/lesmana/webrtc-without-signaling-server

inspired by https://github.com/xem/miniWebRTC

which in turn was inspired by https://github.com/cjb/serverless-webrtc

the minimal SDP 

https://webrtchacks.com/the-minimum-viable-sdp/

v=0
o=- 2088893440337529897 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
a=extmap-allow-mixed
a=msid-semantic: WMS
m=application 9 UDP/DTLS/SCTP webrtc-datachannel
c=IN IP4 0.0.0.0
a=ice-ufrag:R507
a=ice-pwd:1a5CoRVolXGslhsi8QbtJzxZ
a=ice-options:trickle
a=fingerprint:sha-256 E0:F3:54:67:FD:5E:6B:5A:46:ED:C8:08:3F:88:3A:B3:58:FF:2C:31:13:26:8D:93:89:B5:37:34:83:6D:39:88
a=setup:actpass
a=mid:0
a=sctp-port:5000
a=max-message-size:262144

