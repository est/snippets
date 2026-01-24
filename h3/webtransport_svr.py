import asyncio
import ssl
from aioquic.asyncio import serve
from aioquic.h3.connection import H3_ALPN
from aioquic.h3.events import (
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol


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

        # Incoming WebTransport stream data
        elif isinstance(event, WebTransportStreamDataReceived):
            # Reply with "hello world"
            response = b"hello world\n"
            self._quic.send_stream_data(
                event.stream_id,
                response,
                end_stream=True,
            )


async def main():
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=H3_ALPN,
    )

    configuration.load_cert_chain(
        certfile="cert.pem",
        keyfile="key.pem",
    )

    await serve(
        host="localhost",
        port=4433,
        configuration=configuration,
        create_protocol=WebTransportProtocol,
    )

    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

