import ssl
import asyncio
import datetime
import ctypes
import ctypes.util


libssl = ctypes.CDLL(ctypes.util.find_library('ssl'))


def get_ssl_ptr(sslobj):
    """从 _ssl._SSLSocket 获取 SSL* 指针"""
    try:
        class TempPySSLObject(ctypes.Structure):
            _fields_ = [
                ("ob_refcnt", ctypes.c_ssize_t),
                ("ob_type", ctypes.c_void_p),
                ("Socket", ctypes.py_object),
                ("ssl", ctypes.c_void_p),
            ]
        obj_ptr = ctypes.cast(id(sslobj), ctypes.POINTER(TempPySSLObject))
        return obj_ptr.contents.ssl
    except:
        return None


def get_client_ip_from_ssl_socket(ssl_socket):
    """
    从 SSL socket 获取客户端 IP。
    通过遍历 event loop 的 _transports 来查找匹配的连接。
    """
    try:
        ssl_ptr = get_ssl_ptr(ssl_socket)
        print(f"[DEBUG] ssl_ptr={ssl_ptr}")
        if not ssl_ptr:
            return None

        loop = asyncio.get_running_loop()
        print(f"[DEBUG] transports count={len(loop._transports)}")

        # 遍历 loop._transports 找到匹配的 SSL 连接
        for fd, transport in loop._transports.items():
            print(f"[DEBUG] fd={fd}, transport type={type(transport).__name__}")
            # 获取 protocol（对于 SSL 连接，应该是 SSLProtocol）
            protocol = getattr(transport, '_protocol', None)
            print(f"[DEBUG] protocol={protocol}, type={type(protocol).__name__ if protocol else None}")
            if not protocol:
                continue

            # 检查是否是 SSLProtocol
            if not isinstance(protocol, asyncio.sslproto.SSLProtocol):
                continue

            sslpipe = getattr(protocol, '_sslpipe', None)
            print(f"[DEBUG] sslpipe={sslpipe}")
            if not sslpipe:
                continue

            ssl_obj = sslpipe.ssl_object
            print(f"[DEBUG] ssl_obj={ssl_obj}")
            if not ssl_obj or not hasattr(ssl_obj, '_sslobj'):
                continue

            obj_ssl_ptr = get_ssl_ptr(ssl_obj._sslobj)
            print(f"[DEBUG] obj_ssl_ptr={obj_ssl_ptr}, match={obj_ssl_ptr == ssl_ptr}")

            # 比较 SSL 指针
            if obj_ssl_ptr == ssl_ptr:
                sock = transport.get_extra_info('socket')
                if sock:
                    return sock.getpeername()
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()
    return None


def sni_callback(ssl_socket, server_name, ssl_context):
    """
    SNI 回调 - 根据 SNI 决定是否关闭连接，并记录客户端 IP。

    返回 None 表示继续握手，返回 ssl.ALERT_DESCRIPTION_xxx 表示拒绝连接。
    """
    # 获取客户端 IP
    peer = get_client_ip_from_ssl_socket(ssl_socket._sslobj)
    ip = peer[0] if peer else "unknown"
    port = peer[1] if peer else 0

    # 记录日志
    print(f"[{datetime.datetime.now()}] SNI回调: IP={ip}, 端口={port}, SNI={server_name}")

    # 根据 SNI 判断是否关闭连接
    # 示例：拒绝某些 SNI
    blocked_sni = ['blocked.com', 'evil.com']
    if server_name in blocked_sni:
        print(f"[{datetime.datetime.now()}] 拒绝连接: SNI={server_name} 在黑名单中")
        return ssl.ALERT_DESCRIPTION_UNRECOGNIZED_NAME

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
    print(f"[{datetime.datetime.now()}] HTTP处理: {addr}")

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
