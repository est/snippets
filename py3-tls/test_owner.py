import ssl
import asyncio

# 测试：owner 是否指向 SSLObject 本身
def sni_callback(sslobj, server_name, ssl_context):
    owner = sslobj._sslobj.owner
    print(f"sslobj id: {id(sslobj)}")
    print(f"owner id: {id(owner)}")
    print(f"sslobj is owner: {sslobj is owner}")
    return None

async def handle_client(reader, writer):
    writer.write(b"HTTP/1.1 200 OK\r\n\r\nOK")
    await writer.drain()
    writer.close()

async def main():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('server.crt', 'server.key')
    context.sni_callback = sni_callback

    server = await asyncio.start_server(handle_client, '0.0.0.0', 8443, ssl=context)
    print(f"Server on https://0.0.0.0:8443")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
