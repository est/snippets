import asyncio
import ssl
import os
from aioquic.asyncio import serve
from aioquic.h3.connection import H3_ALPN
from aioquic.h3.events import (
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading


class WebTransportProtocol(QuicConnectionProtocol):
    def quic_event_received(self, event):
        # WebTransport session establishment
        if isinstance(event, HeadersReceived):
            headers = dict(event.headers)

            # :method = CONNECT, :protocol = webtransport
            if headers.get(b":method") == b"CONNECT":
                # Accept the session
                self._quic.send_stream_data(
                    event.stream_id,
                    b":status: 200\r\n\r\n",
                    end_stream=False,
                )
            # Handle HTTP requests for static files
            elif headers.get(b":method") == b"GET":
                path = headers.get(b":path", b"/").decode()
                if path == "/":
                    path = "/webtransport_req.html"
                
                file_path = os.path.join(os.getcwd(), path.lstrip("/"))
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                        
                        # Send HTTP response
                        response_headers = [
                            (b":status", b"200"),
                            (b"content-type", b"text/html"),
                            (b"content-length", str(len(content)).encode()),
                        ]
                        
                        self._quic.send_stream_data(
                            event.stream_id,
                            b"\r\n".join([b": ".join(h) for h in response_headers]) + b"\r\n\r\n",
                            end_stream=False,
                        )
                        self._quic.send_stream_data(
                            event.stream_id,
                            content,
                            end_stream=True,
                        )
                    except Exception as e:
                        # Send 500 error
                        error_response = b":status: 500\r\ncontent-type: text/plain\r\n\r\nInternal Server Error"
                        self._quic.send_stream_data(
                            event.stream_id,
                            error_response,
                            end_stream=True,
                        )
                else:
                    # Send 404 error
                    not_found_response = b":status: 404\r\ncontent-type: text/plain\r\n\r\nFile Not Found"
                    self._quic.send_stream_data(
                        event.stream_id,
                        not_found_response,
                        end_stream=True,
                    )

        # Incoming WebTransport stream data
        elif isinstance(event, WebTransportStreamDataReceived):
            # Reply with "hello world"
            response = b"hello world\n"
            self._quic.send_stream_data(
                event.stream_id,
                response,
                end_stream=True,
            )


def start_https_server():
    """启动HTTPS服务器，提供静态文件服务"""
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.path = "/webtransport_req.html"
            return super().do_GET()
    
    # 创建SSL上下文
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    
    # 创建HTTPS服务器
    server = HTTPServer(("localhost", 4433), Handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    print("HTTPS server started on https://localhost:4433")
    server.serve_forever()


async def main():
    # 启动HTTPS服务器线程
    https_thread = threading.Thread(target=start_https_server, daemon=True)
    https_thread.start()
    
    # 配置QUIC/WebTransport服务器
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=H3_ALPN,
    )

    configuration.load_cert_chain(
        certfile="cert.pem",
        keyfile="key.pem",
    )

    print("WebTransport server started on https://localhost:4433")
    await serve(
        host="localhost",
        port=4433,
        configuration=configuration,
        create_protocol=WebTransportProtocol,
    )

    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

