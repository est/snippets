import ssl
import socket
import threading
import datetime


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调函数 - 在 TLS 握手期间获取客户端信息"""
    print(f"\n{'='*60}")
    print(f"[{datetime.datetime.now()}] 收到 TLS 连接")
    print(f"{'='*60}")
    
    # 获取客户端 IP 和端口
    peer = ssl_socket.getpeername()
    print(f"客户端 IP: {peer[0]}")
    print(f"客户端端口: {peer[1]}")
    
    # SNI (Server Name Indication)
    print(f"SNI (服务器名称): {server_name}")
    
    # TLS 版本
    version = ssl_socket.version()
    print(f"TLS 版本: {version}")
    
    # 密码套件
    cipher = ssl_socket.cipher()
    if cipher:
        print(f"密码套件: {cipher[0]}")
        print(f"TLS 版本 (cipher): {cipher[1]}")
        print(f"密钥位数: {cipher[2]}")

    return None


def handle_client(conn, addr):
    """处理客户端连接"""
    print(f"[{datetime.datetime.now()}] 连接已建立: {addr}")
    
    # 接收 HTTP 请求
    data = conn.recv(4096)
    if data:
        request = data.decode('utf-8', errors='ignore')
        print(f"收到请求:\n{request[:500]}...")
        
        # 发送简单的 HTTP 响应
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
    
    context.load_cert_chain(
        certfile='server.crt',
        keyfile='server.key'
    )
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
    print(f"使用 SNI 回调拦截和记录客户端信息")
    print(f"按 Ctrl+C 停止服务器\n")
    print(f"测试命令:")
    print(f"  curl -sk https://localhost:8443")
    print(f"  curl -sk --resolve example.com:8443:127.0.0.1 https://example.com:8443")
    print(f"  openssl s_client -connect localhost:8443 -servername test.com\n")
    
    try:
        while True:
            conn, addr = server_socket.accept()
            
            ssl_conn = context.wrap_socket(conn, server_side=True)
            client_thread = threading.Thread(
                target=handle_client,
                args=(ssl_conn, addr)
            )
            client_thread.daemon = True
            client_thread.start()
                
    except KeyboardInterrupt:
        print("\n服务器停止")
    finally:
        server_socket.close()


if __name__ == '__main__':
    main()
