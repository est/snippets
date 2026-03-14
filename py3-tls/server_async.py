import ssl
import asyncio
import datetime


def get_client_ip(sslobj):
    """在 SNI callback 中获取客户端 IP"""
    # 遍历查找（只会在第一次调用时执行）
    loop = asyncio.get_running_loop()
    for transport in loop._transports.values():
        protocol = getattr(transport, '_protocol', None)
        if protocol and getattr(protocol, '_sslobj', None) is sslobj:
            peername = transport.get_extra_info('peername')
            if peername:
                return peername[0]
    return None


def sni_callback(sslobj, server_name, ssl_context):
    """SNI 回调：记录 IP 并根据 SNI 决定是否拒绝连接"""
    ip = get_client_ip(sslobj) or "unknown"

    print(f"[{datetime.datetime.now()}] SNI: {server_name}, IP: {ip}")

    if server_name in ['blocked.com']:
        print(f"  -> 拒绝连接")
        return ssl.ALERT_DESCRIPTION_UNRECOGNIZED_NAME
    return None


async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[{datetime.datetime.now()}] HTTP: {addr}")

    data = await reader.read(4096)
    if data:
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>OK</h1>")
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def main():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('server.crt', 'server.key')
    context.sni_callback = sni_callback

    server = await asyncio.start_server(handle_client, '0.0.0.0', 8443, ssl=context)
    print(f"HTTPS server on https://0.0.0.0:8443")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
