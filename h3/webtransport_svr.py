import asyncio
import ssl
import os
from aioquic.asyncio.server import serve
from aioquic.h3.connection import H3Connection, H3_ALPN
from aioquic.h3.events import (
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading


class WebTransportProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h3 = None

    def quic_event_received(self, event):
        # Create H3 connection lazily after handshake
        if self._h3 is None:
            self._h3 = H3Connection(self._quic, enable_webtransport=True)
        # Pass QUIC event to H3 connection
        for h3_event in self._h3.handle_event(event):
            self.h3_event_received(h3_event)

    def h3_event_received(self, event):
        if isinstance(event, HeadersReceived):
            headers = dict(event.headers)
            print("Received H3 headers:", headers)

            # WebTransport session establishment
            if headers.get(b":method") == b"CONNECT" and headers.get(b":protocol") == b"webtransport":
                self._h3.send_headers(
                    event.stream_id,
                    [(b":status", b"200"), (b"sec-webtransport-http3-draft", b"draft02")],
                )
                self.transmit()

        elif isinstance(event, WebTransportStreamDataReceived):
            # Only respond if we received actual data (not just the end-stream marker)
            if event.data:
                print(f"WebTransport data received on stream {event.stream_id}: {event.data}")
                # Echo "hello world"
                self._h3._quic.send_stream_data(
                    event.stream_id,
                    b"hello world\n",
                    end_stream=True,
                )
                self.transmit()


def start_https_server():
    """Start HTTPS server for static files."""
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.path = "/webtransport_req.html"
            return super().do_GET()
    
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    
    server = ThreadingHTTPServer(("localhost", 8443), Handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    print("HTTPS server started on https://localhost:8443")
    server.serve_forever()


async def main():
    # Start HTTPS server in a thread
    https_thread = threading.Thread(target=start_https_server, daemon=True)
    https_thread.start()
    
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=H3_ALPN,
    )

    configuration.load_cert_chain(
        certfile="cert.pem",
        keyfile="key.pem",
    )

    print("WebTransport server started on UDP localhost:4433")
    await serve(
        host="::",
        port=4433,
        configuration=configuration,
        create_protocol=WebTransportProtocol,
    )

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

