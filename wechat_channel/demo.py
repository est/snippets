#!/usr/bin/env python3
"""
微信 OpenClaw 通道 API 纯 Python 实现
基于 @tencent-weixin/openclaw-weixin@2.1.8 源码

核心流程与对应源码文件:

1. 扫码登录 (src/auth/login-qr.ts)
   - GET /ilink/bot/get_bot_qrcode?bot_type=3 → 获取二维码
   - GET /ilink/bot/get_qrcode_status?qrcode=xxx → 长轮询状态
   - 状态: wait → scaned → scaned_but_redirect(需切换host) → confirmed → 获取 bot_token
   - 支持二维码过期自动刷新(最多3次)

2. 收消息 (src/api/api.ts:130-162)
   - POST /ilink/bot/getupdates {get_updates_buf}
   - 长轮询 35s 超时，返回 msgs[]

3. 发消息 (src/messaging/send.ts)
   - POST /ilink/bot/sendmessage
   - 结构: {to_user_id, client_id, message_type: 2, message_state: 2, item_list, context_token}
   - context_token 建议填写(可选)

4. 上传图片 (src/cdn/upload.ts, src/cdn/cdn-upload.ts)
   - POST /ilink/bot/getuploadurl → 获取 upload_full_url 或 upload_param
   - AES-128-ECB 加密文件 → POST CDN
   - 从响应头 x-encrypted-param 获取 download_param

常量定义 (src/api/types.ts):
- message_type: 1=USER, 2=BOT
- message_state: 0=NEW, 1=GENERATING, 2=FINISH
- item.type: 1=TEXT, 2=IMAGE, 3=VOICE, 4=FILE, 5=VIDEO
- media_type: 1=IMAGE, 2=VIDEO, 3=FILE, 4=VOICE

默认配置 (src/auth/accounts.ts):
- base_url: https://ilinkai.weixin.qq.com
- cdn_base_url: https://novac2c.cdn.weixin.qq.com/c2c
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import hashlib
import os
import time
import struct
import socket
from typing import Optional


def build_client_version(version: str) -> int:
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    return ((major & 0xFF) << 16) | ((minor & 0xFF) << 8) | (patch & 0xFF)


# 写死。不要从 package/package.json 读
CHANNEL_VERSION = "2.1.8"
ILINK_APP_ID = "bot"
ILINK_APP_CLIENT_VERSION = str(build_client_version(CHANNEL_VERSION))


def is_timeout_error(err: Exception) -> bool:
    reason = getattr(err, "reason", err)
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return True
    return "timed out" in str(reason).lower()


def aes_encrypt(data: bytes, key: bytes) -> bytes:
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
    def __init__(self, token: str = "", base_url: str = "https://ilinkai.weixin.qq.com"):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.sync_buf = ""
        self.longpoll_timeout = 35

    def _uin(self) -> str:
        return base64.b64encode(str(struct.unpack(">I", os.urandom(4))[0]).encode()).decode()

    def _common_headers(self) -> dict:
        return {
            "iLink-App-Id": ILINK_APP_ID,
            "iLink-App-ClientVersion": ILINK_APP_CLIENT_VERSION,
        }

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "X-WECHAT-UIN": self._uin(),
        }
        headers.update(self._common_headers())
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _post(self, endpoint: str, data: dict, timeout: int = 35, allow_timeout: bool = False) -> dict:
        payload = dict(data)
        payload["base_info"] = {"channel_version": CHANNEL_VERSION}
        req = urllib.request.Request(
            f"{self.base_url}/ilink/bot/{endpoint}",
            data=json.dumps(payload).encode(),
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            if allow_timeout and is_timeout_error(e):
                return {"ret": 0, "msgs": [], "get_updates_buf": self.sync_buf}
            raise

    def login(self, timeout: int = 480) -> str:
        qr_req = urllib.request.Request(
            f"{self.base_url}/ilink/bot/get_bot_qrcode?bot_type=3",
            headers=self._common_headers(),
        )
        with urllib.request.urlopen(qr_req) as r:
            qr = json.loads(r.read())

        print(f"[*] 请扫码: {qr['qrcode_img_content']}")

        deadline = time.time() + timeout
        scanned = refresh = False
        polling_url = f"{self.base_url}/ilink/bot/get_qrcode_status"

        while time.time() < deadline:
            url = f"{polling_url}?qrcode={urllib.parse.quote(qr['qrcode'])}"
            req = urllib.request.Request(url, headers=self._common_headers())
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    st = json.loads(r.read())
            except urllib.error.URLError as e:
                if is_timeout_error(e):
                    st = {"status": "wait"}
                else:
                    raise

            status = st.get("status")
            if status == "scaned" and not scanned:
                print("[*] 已扫码，请确认...")
                scanned = True
            elif status == "scaned_but_redirect":
                host = st.get("redirect_host")
                if host:
                    polling_url = f"https://{host}/ilink/bot/get_qrcode_status"
                    print(f"[*] 切换到: {host}")
            elif status == "expired":
                refresh += 1
                if refresh > 3:
                    raise Exception("二维码多次过期")
                print(f"[*] 二维码过期，刷新... ({refresh}/3)")
                scanned = False
                with urllib.request.urlopen(qr_req) as r:
                    qr = json.loads(r.read())
                print(f"[*] 新二维码: {qr['qrcode_img_content']}")
            elif status == "confirmed":
                self.token = st.get("bot_token", "")
                if self.token:
                    print(f"[*] 登录成功: {st.get('ilink_bot_id')}")
                    return self.token
                raise Exception("无 bot_token")

            time.sleep(1)

        raise Exception("登录超时")

    def get_updates(self) -> list:
        resp = self._post(
            "getupdates",
            {"get_updates_buf": self.sync_buf},
            timeout=self.longpoll_timeout,
            allow_timeout=True,
        )
        if resp.get("ret") == 0:
            self.sync_buf = resp.get("get_updates_buf", "")
            timeout_ms = resp.get("longpolling_timeout_ms")
            if isinstance(timeout_ms, int) and timeout_ms > 0:
                self.longpoll_timeout = max(1, (timeout_ms + 999) // 1000)
        return resp.get("msgs", [])

    def send_text(self, to: str, text: str, ctx_token: str = "") -> dict:
        return self._post("sendmessage", {
            "msg": {
                "to_user_id": to,
                "client_id": f"py:{int(time.time()*1000)}-{os.urandom(4).hex()}",
                "message_type": 2,
                "message_state": 2,
                "item_list": [{"type": 1, "text_item": {"text": text}}],
                "context_token": ctx_token or None,
            }
        })

    def upload_image(self, path: str, to: str) -> dict:
        with open(path, "rb") as f:
            plain = f.read()

        key = os.urandom(16)
        cipher = aes_encrypt(plain, key)
        filekey = os.urandom(16).hex()

        resp = self._post("getuploadurl", {
            "filekey": filekey,
            "media_type": 1,
            "to_user_id": to,
            "rawsize": len(plain),
            "rawfilemd5": hashlib.md5(plain).hexdigest(),
            "filesize": len(cipher),
            "no_need_thumb": True,
            "aeskey": key.hex(),
        })

        upload_url = resp.get("upload_full_url", "").strip()
        if not upload_url and resp.get("upload_param"):
            p = resp["upload_param"]
            upload_url = f"https://novac2c.cdn.weixin.qq.com/c2c/upload?encrypted_query_param={urllib.parse.quote(p)}&filekey={filekey}"

        req = urllib.request.Request(
            upload_url,
            data=cipher,
            headers={"Content-Type": "application/octet-stream"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return {
                "download_param": r.headers.get("x-encrypted-param"),
                "aeskey": key.hex(),
                "size": len(cipher),
            }

    def send_image(self, to: str, img_info: dict, ctx_token: str = "") -> dict:
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
                            "encrypt_type": 1,
                        },
                        "mid_size": img_info["size"],
                    }
                }],
                "context_token": ctx_token or None,
            }
        })


def get_text(msg: dict) -> str:
    parts = []
    for item in msg.get("item_list", []):
        if item.get("type") == 1:
            text = item.get("text_item", {}).get("text", "")
            if text:
                parts.append(text)
        if item.get("type") == 3:
            text = item.get("voice_item", {}).get("text", "")
            if text:
                parts.append(text)
    return "\n".join(parts)


def get_media(msg: dict) -> Optional[dict]:
    for item in msg.get("item_list", []):
        if item.get("type") == 2:
            img = item.get("image_item", {})
            return {"type": "image", "url": img.get("url"), "aeskey": img.get("aeskey")}
        if item.get("type") == 4:
            f = item.get("file_item", {})
            return {"type": "file", "name": f.get("file_name"), "len": f.get("len")}
        if item.get("type") == 5:
            v = item.get("video_item", {})
            return {"type": "video", "play_length": v.get("play_length")}
    return None


def summarize_item(item: dict) -> str:
    item_type = item.get("type")

    if item_type == 1:
        text = item.get("text_item", {}).get("text", "")
        return text or "[文本]"

    if item_type == 2:
        img = item.get("image_item", {})
        size = img.get("mid_size") or img.get("hd_size") or img.get("thumb_size")
        return f"[图片 size={size}]" if size else "[图片]"

    if item_type == 3:
        voice = item.get("voice_item", {})
        text = voice.get("text", "")
        if text:
            return f"[语音转文字] {text}"
        playtime = voice.get("playtime")
        return f"[语音 playtime={playtime}ms]" if playtime else "[语音]"

    if item_type == 4:
        file_item = item.get("file_item", {})
        name = file_item.get("file_name") or "unknown"
        length = file_item.get("len")
        return f"[文件] {name} ({length} bytes)" if length else f"[文件] {name}"

    if item_type == 5:
        video = item.get("video_item", {})
        play_length = video.get("play_length")
        return f"[视频 play_length={play_length}ms]" if play_length else "[视频]"

    return f"[未知消息类型 {item_type}]"


def build_echo_text(msg: dict) -> str:
    parts = [summarize_item(item) for item in msg.get("item_list", [])]
    parts = [part for part in parts if part]
    return "\n".join(parts) if parts else "[空消息]"


def main():
    bot = WeixinBot()
    bot.login()

    contexts = {}
    print("[*] 启动回显机器人...")

    while True:
        try:
            for msg in bot.get_updates():
                # print(f'[wechat] {msg}')
                if msg.get("message_type") != 1 or msg.get("message_state") != 0:
                    continue

                user = msg["from_user_id"]
                ctx = msg.get("context_token", "")
                if ctx:
                    contexts[user] = ctx
                ctx_token = ctx or contexts.get(user, "")

                echo_text = build_echo_text(msg)
                print(f"[收] {user}: {echo_text.replace(chr(10), ' | ')}")

                bot.send_text(user, echo_text, ctx_token)
                print(f"[发] {echo_text.replace(chr(10), ' | ')}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
