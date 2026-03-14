import ssl
import asyncio
import datetime
import ctypes


def get_ssl_ptr(sslobj):
    """从 _ssl._SSLSocket 获取 SSL* 指针"""
    class PySSLSocket(ctypes.Structure):
        _fields_ = [("ob_refcnt", ctypes.c_ssize_t), ("ob_type", ctypes.c_void_p),
                    ("Socket", ctypes.py_object), ("ssl", ctypes.c_void_p)]
    return ctypes.cast(id(sslobj), ctypes.POINTER(PySSLSocket)).contents.ssl


def get_client_ip(sslobj):
    """在 SNI callback 中获取客户端 IP"""
    # import pdb;pdb.set_trace()
    # ssl_ptr = get_ssl_ptr(sslobj._sslobj)
    owner = sslobj._sslobj.owner
    loop = asyncio.get_running_loop()

    for transport in loop._transports.values():
        protocol = getattr(transport, '_protocol', None)
        # import pdb;pdb.set_trace()
        if not protocol or not hasattr(protocol, '_sslobj'):
            continue
        # if get_ssl_ptr(protocol._sslobj) == owner:
        if protocol._sslobj == owner:
            return transport.get_extra_info('peername')
    return None


def sni_callback(sslobj, server_name, ssl_context):
    """SNI 回调：记录 IP 并根据 SNI 决定是否拒绝连接"""
    peer = get_client_ip(sslobj)
    ip = peer[0] if peer else "unknown"

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
