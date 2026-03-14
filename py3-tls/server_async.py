import ssl
import asyncio
import datetime
import ctypes
import ctypes.util


libssl = ctypes.CDLL(ctypes.util.find_library('ssl'))

# 尝试从 SSLObject 获取 socket fd
libssl.SSL_get_fd.argtypes = [ctypes.c_void_p]
libssl.SSL_get_fd.restype = ctypes.c_int


class PySSLObject(ctypes.Structure):
    """Python SSLObject 结构"""
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
        ("ssl", ctypes.c_void_p),  # SSL*
        ("ctx", ctypes.c_void_p),  # SSL_CTX*
        ("socket", ctypes.py_object),  # Python socket 对象
        ("owner", ctypes.py_object),
        ("state", ctypes.c_int),
    ]


def get_peer_from_ssl_object(ssl_obj):
    """从 SSLObject 获取对端地址"""
    try:
        # 方法1: 尝试直接访问 _sslobj 的 socket
        if hasattr(ssl_obj, '_sslobj'):
            sslobj = ssl_obj._sslobj
            # 打印可用属性看看
            # print(f"sslobj attrs: {[a for a in dir(sslobj) if not a.startswith('__')]}")
            if hasattr(sslobj, 'getpeername'):
                return sslobj.getpeername()
            if hasattr(sslobj, '_socket'):
                return sslobj._socket.getpeername()
            if hasattr(sslobj, 'socket'):
                return sslobj.socket.getpeername()
        
        # 方法2: 通过 ctypes 获取 SSL* 指针，然后 SSL_get_fd
        if hasattr(ssl_obj, '_sslobj') and ssl_obj._sslobj:
            # 获取 SSL* 指针
            sslobj = ssl_obj._sslobj
            # 构造 PySSLObject 来读取 ssl 字段
            class TempPySSLObject(ctypes.Structure):
                _fields_ = [
                    ("ob_refcnt", ctypes.c_ssize_t),
                    ("ob_type", ctypes.c_void_p),
                    ("ssl", ctypes.c_void_p),
                ]
            obj_ptr = ctypes.cast(id(sslobj), ctypes.POINTER(TempPySSLObject))
            ssl_ptr = obj_ptr.contents.ssl
            if ssl_ptr:
                fd = libssl.SSL_get_fd(ssl_ptr)
                if fd >= 0:
                    import socket
                    # 用 getsockname 获取本地地址，getpeername 需要对端已连接
                    # 这里 fd 是底层的 socket fd
                    try:
                        sock = socket.socket(fileno=fd)
                        peer = sock.getpeername()
                        sock.detach()  # 不要关闭 fd
                        return peer
                    except:
                        pass
    except Exception as e:
        # print(f"get_peer error: {e}")
        pass
    return None


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调 - 打印客户端信息"""
    ip = "unknown"
    port = 0
    
    # 尝试获取对端地址
    peer = get_peer_from_ssl_object(ssl_socket)
    if peer:
        ip, port = peer[0], peer[1]
    
    print(f"[{datetime.datetime.now()}] SNI回调: IP={ip}, 端口={port}, SNI={server_name}")
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
