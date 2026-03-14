import ssl
import socket
import threading
import datetime
import ctypes
import ctypes.util
import struct


# 加载 OpenSSL 库
libssl_path = ctypes.util.find_library('ssl')
libssl = ctypes.CDLL(libssl_path)

libcrypto_path = ctypes.util.find_library('crypto')
libcrypto = ctypes.CDLL(libcrypto_path)

# OpenSSL 函数定义
libssl.SSL_get_client_ciphers.argtypes = [ctypes.c_void_p]
libssl.SSL_get_client_ciphers.restype = ctypes.c_void_p

libssl.SSL_get_client_random.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
libssl.SSL_get_client_random.restype = ctypes.c_size_t

libssl.SSL_get_version.argtypes = [ctypes.c_void_p]
libssl.SSL_get_version.restype = ctypes.c_char_p

# OpenSSL 3.x 函数名加了 OPENSSL_ 前缀
try:
    libcrypto.OPENSSL_sk_num.argtypes = [ctypes.c_void_p]
    libcrypto.OPENSSL_sk_num.restype = ctypes.c_int
    libcrypto.OPENSSL_sk_value.argtypes = [ctypes.c_void_p, ctypes.c_int]
    libcrypto.OPENSSL_sk_value.restype = ctypes.c_void_p
    sk_num = libcrypto.OPENSSL_sk_num
    sk_value = libcrypto.OPENSSL_sk_value
except AttributeError:
    # OpenSSL 1.x
    libcrypto.sk_num.argtypes = [ctypes.c_void_p]
    libcrypto.sk_num.restype = ctypes.c_int
    libcrypto.sk_value.argtypes = [ctypes.c_void_p, ctypes.c_int]
    libcrypto.sk_value.restype = ctypes.c_void_p
    sk_num = libcrypto.sk_num
    sk_value = libcrypto.sk_value

libssl.SSL_CIPHER_get_name.argtypes = [ctypes.c_void_p]
libssl.SSL_CIPHER_get_name.restype = ctypes.c_char_p

libssl.SSL_CIPHER_get_version.argtypes = [ctypes.c_void_p]
libssl.SSL_CIPHER_get_version.restype = ctypes.c_char_p


class PySSLObject(ctypes.Structure):
    """Python _ssl.SSLSocket 对象结构 (简化版)"""
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
        ("ssl", ctypes.c_void_p),  # SSL* 指针
        ("ctx", ctypes.c_void_p),  # SSL_CTX*
        ("socket", ctypes.py_object),
        ("handshake_done", ctypes.c_int),
    ]


def get_ssl_ptr_from_socket(ssl_socket):
    """从 Python SSLSocket 获取 OpenSSL SSL* 指针"""
    sslobj = ssl_socket._sslobj
    if sslobj is None:
        return None
    
    # 解包 _SSLSocket 对象获取 SSL* 指针
    # 在 CPython 中，PySSLObject 结构以 ssl 字段开头
    obj_ptr = ctypes.cast(id(sslobj), ctypes.POINTER(PySSLObject))
    return obj_ptr.contents.ssl


def get_client_ciphers(ssl_ptr):
    """获取客户端 ClientHello 中的密码套件列表"""
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
            version = libssl.SSL_CIPHER_get_version(cipher)
            name_str = name.decode('utf-8') if name else 'unknown'
            version_str = version.decode('utf-8') if version else 'unknown'
            result.append((name_str, version_str))
    return result


def get_tls_version(ssl_ptr):
    """获取 TLS 版本"""
    if not ssl_ptr:
        return None
    version = libssl.SSL_get_version(ssl_ptr)
    return version.decode('utf-8') if version else None


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调函数 - 在 TLS 握手期间获取客户端信息"""
    print(f"\n{'='*60}")
    print(f"[{datetime.datetime.now()}] 收到 TLS 连接 (SNI 回调)")
    print(f"{'='*60}")
    
    peer = ssl_socket.getpeername()
    print(f"客户端 IP: {peer[0]}")
    print(f"客户端端口: {peer[1]}")
    print(f"SNI: {server_name}")
    
    # 获取 SSL* 指针
    ssl_ptr = get_ssl_ptr_from_socket(ssl_socket)
    print(f"SSL* 指针: {hex(ssl_ptr) if ssl_ptr else 'None'}")
    
    if ssl_ptr:
        # TLS 版本
        tls_version = get_tls_version(ssl_ptr)
        print(f"TLS 版本: {tls_version}")
        
        # 客户端支持的密码套件
        client_ciphers = get_client_ciphers(ssl_ptr)
        print(f"\n客户端支持的密码套件 ({len(client_ciphers)} 个):")
        for name, ver in client_ciphers[:15]:
            print(f"  {name} [{ver}]")
        if len(client_ciphers) > 15:
            print(f"  ... 还有 {len(client_ciphers) - 15} 个")
    
    print(f"{'='*60}\n")
    return None


def handle_client(conn, addr):
    """处理客户端连接"""
    print(f"[{datetime.datetime.now()}] 连接已建立: {addr}")
    
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
    """创建 SSL 上下文并配置 SNI 回调"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')
    print("证书加载成功")
    context.sni_callback = sni_callback
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def generate_self_signed_cert():
    """自动生成自签名证书"""
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
