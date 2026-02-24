import asyncio
from aioquic.asyncio import connect
from aioquic.h3.connection import H3_ALPN

async def main():
    async with connect(
        "localhost",
        4433,
        configuration=None,
        # alpn_protocols=H3_ALPN,
        # create_protocol=None
    ) as protocol:
        print("Connected")

asyncio.run(main())
