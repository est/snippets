import ssl
import asyncio
import datetime
import ctypes
import ctypes.util


libssl = ctypes.CDLL(ctypes.util.find_library('ssl'))


# 全局字典：SSL 指针 -> peername
_ssl_peername_map = {}


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


def get_ssl_object(protocol):
    """从 SSLProtocol 获取 SSLObject（兼容 Python 3.9 和 3.12+）"""
    # Python 3.12+: _sslobj 直接存储 SSLObject
    if hasattr(protocol, '_sslobj'):
        return protocol._sslobj
    # Python 3.9: 通过 _sslpipe.ssl_object 获取
    sslpipe = getattr(protocol, '_sslpipe', None)
    if sslpipe:
        return sslpipe.ssl_object
    return None


def find_peername_for_ssl(ssl_socket):
    """
    通过遍历 transport 找到 SSL socket 对应的 peername。
    """
    try:
        ssl_ptr = get_ssl_ptr(ssl_socket)
        if not ssl_ptr:
            return None

        # 检查是否已有映射
        if ssl_ptr in _ssl_peername_map:
            return _ssl_peername_map[ssl_ptr]

        loop = asyncio.get_running_loop()

        # 遍历所有 transport
        for fd, transport in loop._transports.items():
            protocol = getattr(transport, '_protocol', None)
            if not protocol:
                continue

            # 获取 SSLObject
            ssl_obj = get_ssl_object(protocol)
            if not ssl_obj or not hasattr(ssl_obj, '_sslobj'):
                continue

            # 比较 SSL 指针
            if get_ssl_ptr(ssl_obj._sslobj) == ssl_ptr:
                # 找到匹配的 transport，获取 peername
                peername = transport.get_extra_info('peername')
                if peername:
                    # 记录映射
                    _ssl_peername_map[ssl_ptr] = peername
                    return peername
    except:
        pass
    return None


def sni_callback(ssl_socket, server_name, ssl_context):
    """
    SNI 回调 - 根据 SNI 决定是否关闭连接，并记录客户端 IP。
    """
    peer = find_peername_for_ssl(ssl_socket._sslobj)
    ip = peer[0] if peer else "unknown"
    port = peer[1] if peer else 0

    print(f"[{datetime.datetime.now()}] SNI回调: IP={ip}, 端口={port}, SNI={server_name}")

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
