import ssl
import datetime
from fastapi import FastAPI, Request
from uvicorn import Config, Server

app = FastAPI()


def sni_callback(ssl_socket, server_name, ssl_context):
    """SNI 回调 - 打印客户端信息"""
    peer = ssl_socket.getpeername()
    print(f"[{datetime.datetime.now()}] SNI回调: IP={peer[0]}, 端口={peer[1]}, SNI={server_name}")
    return None


def create_ssl_context():
    """创建 SSL 上下文"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')
    context.sni_callback = sni_callback
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


@app.get("/")
async def root(request: Request):
    client = request.client
    print(f"[{datetime.datetime.now()}] HTTP请求: IP={client.host}, 端口={client.port}")
    return {"message": "Hello from Uvicorn HTTPS Server!"}


if __name__ == "__main__":
    ssl_context = create_ssl_context()

    config = Config(
        app=app,
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="server.key",
        ssl_certfile="server.crt",
    )

    # 手动设置 ssl_context 以使用我们的 sni_callback
    config.ssl = ssl_context

    server = Server(config)
    print(f"Uvicorn HTTPS 服务器启动在 https://0.0.0.0:8443")
    print(f"测试: curl -sk https://localhost:8443")
    server.run()
