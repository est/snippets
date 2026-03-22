#!/usr/bin/env python3
"""
微信 OpenClaw 通道 API 纯 Python 实现
基于 @tencent-weixin/openclaw-weixin@1.0.2 源码分析

核心流程与对应源码文件:

1. 认证头生成 (src/api/api.ts:35-48)
   - X-WECHAT-UIN: 随机 uint32 -> 十进制字符串 -> base64
   - Authorization: Bearer <token>
   - AuthorizationType: ilink_bot_token
   - 每个请求带 base_info: {channel_version: "x.x.x"}

2. 长轮询收消息 (src/api/api.ts:130-162)
   - POST /ilink/bot/getupdates
   - 请求: {get_updates_buf: "游标"}
   - 响应: {ret, msgs[], get_updates_buf, longpolling_timeout_ms}
   - 客户端超时后重试是正常的

3. 发送文本消息 (src/messaging/send.ts:70-95)
   - POST /ilink/bot/sendmessage
   - 必须字段: context_token (从收到的消息中获取)
   - 消息结构: {to_user_id, client_id, message_type: 2(BOT), message_state: 2(FINISH), item_list, context_token}

4. 上传图片到 CDN (src/cdn/upload.ts:50-78, src/cdn/cdn-upload.ts:18-77)
   - 步骤1: POST /ilink/bot/getuploadurl 获取 upload_param
   - 步骤2: AES-128-ECB 加密文件 (PKCS7 padding)
   - 步骤3: POST https://novac2c.cdn.weixin.qq.com/c2c/upload 上传密文
   - 步骤4: 从响应头 x-encrypted-param 获取 download_param

5. 发送图片消息 (src/messaging/send.ts:140-170)
   - POST /ilink/bot/sendmessage
   - item_list 包含 image_item: {media: {encrypt_query_param, aes_key(base64), encrypt_type: 1}, mid_size}

消息类型定义 (src/api/types.ts:15-75):
- message_type: 1=USER, 2=BOT
- message_state: 0=NEW, 1=GENERATING, 2=FINISH
- item.type: 1=TEXT, 2=IMAGE, 3=VOICE, 4=FILE, 5=VIDEO

默认配置 (src/auth/accounts.ts:13-14):
- base_url: https://ilinkai.weixin.qq.com
- cdn_base_url: https://novac2c.cdn.weixin.qq.com/c2c
"""

import urllib.request
import urllib.error
import json
import base64
import hashlib
import os
import time
import struct


def aes_encrypt(data: bytes, key: bytes) -> bytes:
    """AES-128-ECB 加密 (PKCS7 padding)"""
    pad = 16 - (len(data) % 16)
    padded = data + bytes([pad] * pad)
    try:
        from Crypto.Cipher import AES
        return AES.new(key, AES.MODE_ECB).encrypt(padded)
    except ImportError:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        return cipher.encryptor().update(padded) + cipher.encryptor().finalize()


class WeixinBot:
    """微信机器人客户端"""

    def __init__(self, token: str, base_url: str = "https://ilinkai.weixin.qq.com"):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.sync_buf = ""

    def _uin(self) -> str:
        """生成 X-WECHAT-UIN: 随机 uint32 -> 十进制字符串 -> base64"""
        return base64.b64encode(str(struct.unpack('>I', os.urandom(4))[0]).encode()).decode()

    def _post(self, endpoint: str, data: dict, timeout: int = 35) -> dict:
        """发送 POST 请求"""
        data["base_info"] = {"channel_version": "1.0.2"}
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{self.base_url}/ilink/bot/{endpoint}",
            data=body,
            headers={
                "Content-Type": "application/json",
                "AuthorizationType": "ilink_bot_token",
                "Authorization": f"Bearer {self.token}",
                "X-WECHAT-UIN": self._uin(),
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError:
            return {"ret": 0, "msgs": []}

    def get_updates(self) -> list:
        """长轮询获取消息"""
        resp = self._post("getupdates", {"get_updates_buf": self.sync_buf})
        if resp.get("ret") == 0:
            self.sync_buf = resp.get("get_updates_buf", "")
        return resp.get("msgs", [])

    def send_text(self, to: str, text: str, ctx_token: str) -> dict:
        """发送文本消息"""
        return self._post("sendmessage", {
            "msg": {
                "to_user_id": to,
                "client_id": f"py:{int(time.time()*1000)}-{os.urandom(4).hex()}",
                "message_type": 2,  # BOT
                "message_state": 2,  # FINISH
                "item_list": [{"type": 1, "text_item": {"text": text}}],
                "context_token": ctx_token
            }
        })

    def upload_image(self, path: str, to: str) -> dict:
        """上传图片到 CDN"""
        with open(path, 'rb') as f:
            plain = f.read()

        key = os.urandom(16)
        cipher = aes_encrypt(plain, key)
        filekey = os.urandom(16).hex()

        url = self._post("getuploadurl", {
            "filekey": filekey,
            "media_type": 1,
            "to_user_id": to,
            "rawsize": len(plain),
            "rawfilemd5": hashlib.md5(plain).hexdigest(),
            "filesize": len(cipher),
            "no_need_thumb": True,
            "aeskey": key.hex()
        }).get("upload_param")

        req = urllib.request.Request(
            f"https://novac2c.cdn.weixin.qq.com/c2c/upload?encrypted_query_param={urllib.parse.quote(url)}&filekey={filekey}",
            data=cipher,
            headers={"Content-Type": "application/octet-stream"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return {
                "download_param": r.headers.get("x-encrypted-param"),
                "aeskey": key.hex(),
                "size": len(cipher)
            }

    def send_image(self, to: str, img_info: dict, ctx_token: str):
        """发送图片消息"""
        return self._post("sendmessage", {
            "msg": {
                "to_user_id": to,
                "client_id": f"py:{int(time.time()*1000)}-{os.urandom(4).hex()}",
                "message_type": 2,
                "message_state": 2,
                "item_list": [{
                    "type": 2,
                    "image_item": {
                        "media": {
                            "encrypt_query_param": img_info["download_param"],
                            "aes_key": base64.b64encode(bytes.fromhex(img_info["aeskey"])).decode(),
                            "encrypt_type": 1
                        },
                        "mid_size": img_info["size"]
                    }
                }],
                "context_token": ctx_token
            }
        })


def get_text(msg: dict) -> str:
    """提取消息文本"""
    for item in msg.get("item_list", []):
        if item.get("type") == 1:
            return item.get("text_item", {}).get("text", "")
        if item.get("type") == 3:
            return item.get("voice_item", {}).get("text", "")
    return ""


def main():
    """回显机器人示例"""
    bot = WeixinBot("your_token_here")
    contexts = {}

    print("[*] 启动回显机器人...")
    while True:
        try:
            for msg in bot.get_updates():
                if msg.get("message_type") != 1 or msg.get("message_state") != 0:
                    continue

                user = msg["from_user_id"]
                ctx = msg.get("context_token", "")
                if ctx:
                    contexts[user] = ctx

                text = get_text(msg)
                print(f"[收] {user}: {text}")

                if text and user in contexts:
                    bot.send_text(user, f"Echo: {text}", contexts[user])
                    print(f"[发] Echo: {text}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
