import ssl
import asyncio
import datetime
import ctypes
import ctypes.util


libssl = ctypes.CDLL(ctypes.util.find_library('ssl'))

# SSL_get_fd 获取底层 socket fd
libssl.SSL_get_fd.argtypes = [ctypes.c_void_p]
libssl.SSL_get_fd.restype = ctypes.c_int


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


def get_all_ssl_transports():
    """从 event loop 获取所有 SSL transport"""
    transports = []
    try:
        loop = asyncio.get_running_loop()
        # loop._transports 是一个 WeakValueDictionary，key 是 fd，value 是 transport
        for fd, transport in loop._transports.items():
            # 检查是否是 SSL transport（即 SSLProtocol 的 _app_transport）
            if hasattr(transport, '_ssl_protocol'):
                transports.append((fd, transport))
    except:
        pass
    return transports


def find_socket_for_ssl_socket(ssl_socket):
    """通过 event loop 的 _transports 查找对应的 socket"""
    try:
        # 获取 SSL 指针
        ssl_ptr = get_ssl_ptr(ssl_socket)
        if not ssl_ptr:
            return None

        # 遍历所有 SSL transport
        for fd, transport in get_all_ssl_transports():
            ssl_protocol = transport._ssl_protocol
            if ssl_protocol:
                sslpipe = getattr(ssl_protocol, '_sslpipe', None)
                if sslpipe:
                    ssl_obj = sslpipe.ssl_object
                    if ssl_obj and hasattr(ssl_obj, '_sslobj'):
                        obj_ssl_ptr = get_ssl_ptr(ssl_obj._sslobj)
                        if obj_ssl_ptr == ssl_ptr:
                            # 找到了，获取 transport 的 socket
                            return transport.get_extra_info('socket')
    except:
        pass
    return None


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调 - 打印客户端信息"""
    peer = None

    # 方法: 通过 event loop 的 _transports 查找对应的 socket
    try:
        sock = find_socket_for_ssl_socket(ssl_socket._sslobj)
        if sock:
            peer = sock.getpeername()
    except:
        pass

    if peer:
        ip, port = peer
        print(f"[{datetime.datetime.now()}] SNI回调: IP={ip}, 端口={port}, SNI={server_name}")
    else:
        print(f"[{datetime.datetime.now()}] SNI回调: IP=unknown, 端口=0, SNI={server_name}")

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
