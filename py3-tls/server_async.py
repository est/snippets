import ssl
import asyncio
import datetime


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调 - 打印客户端信息"""
    # asyncio 里 ssl_socket 是 SSLObject，需要通过 context 获取信息
    # 或者直接用 server_name
    print(f"[{datetime.datetime.now()}] SNI回调: SNI={server_name}")
    return None


def create_ssl_context():
    """创建 SSL 上下文"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')
    context.sni_callback = sni_callback
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


async def handle_client(reader, writer):
    """处理客户端请求"""
    addr = writer.get_extra_info('peername')
    print(f"[{datetime.datetime.now()}] 连接建立: {addr}")

    data = await reader.read(4096)
    if data:
        request = data.decode('utf-8', errors='ignore')
        print(f"收到请求: {request.split()[0] if request else 'empty'} {request.split()[1] if len(request.split()) > 1 else ''}")

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n"
            "\r\n"
            "<h1>Hello from Async HTTPS Server!</h1>"
        )
        writer.write(response.encode())
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def main():
    context = create_ssl_context()

    server = await asyncio.start_server(
        handle_client,
        '0.0.0.0', 8443,
        ssl=context
    )

    print(f"Async HTTPS 服务器启动在 https://0.0.0.0:8443")
    print(f"测试: curl -sk https://localhost:8443")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
