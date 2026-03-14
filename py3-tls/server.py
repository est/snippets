import ssl
import socket
import threading
import datetime
import ctypes
import ctypes.util


libssl = ctypes.CDLL(ctypes.util.find_library('ssl'))
libcrypto = ctypes.CDLL(ctypes.util.find_library('crypto'))

# OpenSSL 3.x 兼容
sk_num = getattr(libcrypto, 'OPENSSL_sk_num', getattr(libcrypto, 'sk_num', None))
sk_value = getattr(libcrypto, 'OPENSSL_sk_value', getattr(libcrypto, 'sk_value', None))

libssl.SSL_get_client_ciphers.argtypes = [ctypes.c_void_p]
libssl.SSL_get_client_ciphers.restype = ctypes.c_void_p
libssl.SSL_get_shared_ciphers.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
libssl.SSL_get_shared_ciphers.restype = ctypes.c_char_p
libssl.SSL_get_version.argtypes = [ctypes.c_void_p]
libssl.SSL_get_version.restype = ctypes.c_char_p
libssl.SSL_get_current_cipher.argtypes = [ctypes.c_void_p]
libssl.SSL_get_current_cipher.restype = ctypes.c_void_p
libssl.SSL_CIPHER_get_name.argtypes = [ctypes.c_void_p]
libssl.SSL_CIPHER_get_name.restype = ctypes.c_char_p
libssl.SSL_CIPHER_get_version.argtypes = [ctypes.c_void_p]
libssl.SSL_CIPHER_get_version.restype = ctypes.c_char_p
libssl.SSL_get_session.argtypes = [ctypes.c_void_p]
libssl.SSL_get_session.restype = ctypes.c_void_p
libssl.SSL_SESSION_get_protocol_version.argtypes = [ctypes.c_void_p]
libssl.SSL_SESSION_get_protocol_version.restype = ctypes.c_int
libssl.SSL_get0_alpn_selected.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)), ctypes.POINTER(ctypes.c_size_t)]
libssl.SSL_get0_alpn_selected.restype = None


class PySSLObject(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
        ("ssl", ctypes.c_void_p),
        ("ctx", ctypes.c_void_p),
        ("socket", ctypes.py_object),
        ("handshake_done", ctypes.c_int),
    ]


def get_ssl_ptr(ssl_socket):
    sslobj = ssl_socket._sslobj
    if sslobj is None:
        return None
    obj_ptr = ctypes.cast(id(sslobj), ctypes.POINTER(PySSLObject))
    return obj_ptr.contents.ssl


def get_client_ciphers(ssl_ptr):
    if not ssl_ptr:
        return []
    ciphers = libssl.SSL_get_client_ciphers(ssl_ptr)
    if not ciphers:
        return []
    count = sk_num(ciphers)
    result = []
    for i in range(count):
        cipher = sk_value(ciphers, i)
        if cipher:
            name = libssl.SSL_CIPHER_get_name(cipher)
            name_str = name.decode('utf-8') if name else 'unknown'
            result.append(name_str)
    return result


def get_session_version(ssl_ptr):
    """从 SSL Session 获取协议版本"""
    if not ssl_ptr:
        return None
    session = libssl.SSL_get_session(ssl_ptr)
    if not session:
        return None
    ver = libssl.SSL_SESSION_get_protocol_version(session)
    ver_map = {0x0301: 'TLSv1', 0x0302: 'TLSv1.1', 0x0303: 'TLSv1.2', 0x0304: 'TLSv1.3'}
    return ver_map.get(ver, f'0x{ver:04x}')


def get_alpn(ssl_ptr):
    """获取 ALPN 协商结果"""
    if not ssl_ptr:
        return None
    data = ctypes.POINTER(ctypes.c_ubyte)()
    len_ = ctypes.c_size_t()
    libssl.SSL_get0_alpn_selected(ssl_ptr, ctypes.byref(data), ctypes.byref(len_))
    if data and len_.value > 0:
        return bytes(data[:len_.value]).decode('utf-8', errors='ignore')
    return None


def sni_callback(ssl_socket, server_name, ssl_context):
    print(f"\n{'='*60}")
    print(f"[{datetime.datetime.now()}] SNI 回调触发")
    print(f"{'='*60}")

    peer = ssl_socket.getpeername()
    print(f"客户端 IP: {peer[0]}")
    print(f"客户端端口: {peer[1]}")
    print(f"SNI: {server_name}")

    ssl_ptr = get_ssl_ptr(ssl_socket)
    print(f"SSL* 指针: {hex(ssl_ptr) if ssl_ptr else 'None'}")

    if ssl_ptr:
        # 尝试获取 session 版本 (TLS 1.3 早期数据可能有用)
        session_ver = get_session_version(ssl_ptr)
        print(f"Session 协议版本: {session_ver}")

        # ALPN
        alpn = get_alpn(ssl_ptr)
        print(f"ALPN: {alpn}")

        # 客户端密码套件 (SNI 回调时通常为空)
        client_ciphers = get_client_ciphers(ssl_ptr)
        print(f"客户端密码套件数量: {len(client_ciphers)}")
        if client_ciphers:
            for c in client_ciphers[:10]:
                print(f"  - {c}")

    print(f"{'='*60}\n")
    return None


def handle_client(conn, addr):
    print(f"[{datetime.datetime.now()}] 连接已建立: {addr}")

    # 握手完成后可以获取更多信息
    ssl_ptr = get_ssl_ptr(conn)
    if ssl_ptr:
        version = libssl.SSL_get_version(ssl_ptr)
        cipher = libssl.SSL_get_current_cipher(ssl_ptr)
        cipher_name = libssl.SSL_CIPHER_get_name(cipher) if cipher else b'none'
        print(f"  最终 TLS 版本: {version.decode() if version else 'unknown'}")
        print(f"  选定密码套件: {cipher_name.decode() if cipher_name else 'unknown'}")

    data = conn.recv(4096)
    if data:
        request = data.decode('utf-8', errors='ignore')
        print(f"收到请求:\n{request[:500]}...")

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n"
            "\r\n"
            "<h1>Hello from HTTPS Server!</h1>"
            "<p>TLS 握手信息已在服务器日志中打印</p>"
        )
        conn.sendall(response.encode())

    conn.close()


def create_ssl_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')
    print("证书加载成功")
    context.sni_callback = sni_callback
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def generate_self_signed_cert():
    import subprocess
    import os
    if os.path.exists('server.crt') and os.path.exists('server.key'):
        print("证书文件已存在")
        return True
    print("正在生成自签名证书...")
    subprocess.run([
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
        '-keyout', 'server.key', '-out', 'server.crt',
        '-days', '365', '-nodes',
        '-subj', '/CN=localhost/O=Test/C=US'
    ], check=True, capture_output=True)
    print("自签名证书生成成功")
    return True


def main():
    generate_self_signed_cert()
    context = create_ssl_context()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8443))
    server_socket.listen(5)

    print(f"\nHTTPS 服务器启动在 https://0.0.0.0:8443")
    print(f"按 Ctrl+C 停止服务器\n")
    print(f"测试命令:")
    print(f"  curl -sk https://localhost:8443")
    print(f"  curl -sk --resolve test.com:8443:127.0.0.1 https://test.com:8443")

    try:
        while True:
            conn, addr = server_socket.accept()
            ssl_conn = context.wrap_socket(conn, server_side=True)
            client_thread = threading.Thread(target=handle_client, args=(ssl_conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n服务器停止")
    finally:
        server_socket.close()


if __name__ == '__main__':
    main()
