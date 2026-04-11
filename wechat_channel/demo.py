#!/usr/bin/env python3
"""
微信 OpenClaw 通道 API 纯 Python 实现
基于 @tencent-weixin/openclaw-weixin@2.1.8 源码
"""

import base64
import hashlib
import json
import os
import socket
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional


class MessageType:
    USER = 1
    BOT = 2


class MessageState:
    NEW = 0
    GENERATING = 1
    FINISH = 2


class ItemType:
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    FILE = 4
    VIDEO = 5


class MediaType:
    IMAGE = 1
    VIDEO = 2
    FILE = 3
    VOICE = 4


SESSION_FILE = ".session"
CHANNEL_VERSION = "2.1.8"
ILINK_APP_ID = "bot"
DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
DEFAULT_CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"


def build_client_version(version: str) -> int:
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    return ((major & 0xFF) << 16) | ((minor & 0xFF) << 8) | (patch & 0xFF)


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
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()


class WeixinClawBot:
    def __init__(
        self,
        token: str = "",
        base_url: str = DEFAULT_BASE_URL,
        cdn_base_url: str = DEFAULT_CDN_BASE_URL,
        session_file: str = SESSION_FILE,
    ):
        self.base_url = base_url.rstrip("/")
        self.cdn_base_url = cdn_base_url.rstrip("/")
        self.session_file = session_file
        self.token = token
        self.sync_buf = ""
        self.longpoll_timeout = 35

    @staticmethod
    def load_session_token(session_file: str = SESSION_FILE) -> Optional[str]:
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                return f.read().strip()
        return None

    @classmethod
    def from_session(
        cls,
        session_file: str = SESSION_FILE,
        base_url: str = DEFAULT_BASE_URL,
        cdn_base_url: str = DEFAULT_CDN_BASE_URL,
    ) -> "WeixinClawBot":
        token = cls.load_session_token(session_file) or ""
        return cls(
            token=token,
            base_url=base_url,
            cdn_base_url=cdn_base_url,
            session_file=session_file,
        )

    def save_session(self, token: Optional[str] = None) -> None:
        session_token = token if token is not None else self.token
        if not session_token:
            return
        with open(self.session_file, "w") as f:
            f.write(session_token)

    def _uin(self) -> str:
        value = struct.unpack(">I", os.urandom(4))[0]
        return base64.b64encode(str(value).encode()).decode()

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

    def _build_client_id(self) -> str:
        return f"py:{int(time.time() * 1000)}-{os.urandom(4).hex()}"

    def _post(
        self,
        endpoint: str,
        data: dict,
        timeout: int = 35,
        allow_timeout: bool = False,
    ) -> dict:
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

    def _send_items(self, to: str, items: list, ctx_token: str = "") -> dict:
        last_resp = {}
        for item in items:
            msg = {
                "to_user_id": to,
                "client_id": self._build_client_id(),
                "message_type": MessageType.BOT,
                "message_state": MessageState.FINISH,
                "item_list": [item],
            }
            if ctx_token:
                msg["context_token"] = ctx_token
            last_resp = self._post("sendmessage", {"msg": msg})
        return last_resp

    def _resolve_upload_url(self, resp: dict, filekey: str) -> str:
        upload_url = resp.get("upload_full_url", "").strip()
        if upload_url:
            return upload_url

        upload_param = resp.get("upload_param")
        if upload_param:
            return (
                f"{self.cdn_base_url}/upload"
                f"?encrypted_query_param={urllib.parse.quote(upload_param)}"
                f"&filekey={filekey}"
            )

        raise Exception("getuploadurl 未返回 upload_full_url/upload_param")

    def _upload_media(self, path: str, to: str, media_type: int) -> dict:
        with open(path, "rb") as f:
            plain = f.read()

        key = os.urandom(16)
        cipher = aes_encrypt(plain, key)
        filekey = os.urandom(16).hex()

        resp = self._post(
            "getuploadurl",
            {
                "filekey": filekey,
                "media_type": media_type,
                "to_user_id": to,
                "rawsize": len(plain),
                "rawfilemd5": hashlib.md5(plain).hexdigest(),
                "filesize": len(cipher),
                "no_need_thumb": True,
                "aeskey": key.hex(),
            },
        )

        upload_url = self._resolve_upload_url(resp, filekey)
        req = urllib.request.Request(
            upload_url,
            data=cipher,
            headers={"Content-Type": "application/octet-stream"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            download_param = r.headers.get("x-encrypted-param")
            if not download_param:
                raise Exception("CDN 上传成功但缺少 x-encrypted-param")
            return {
                "download_param": download_param,
                "aeskey": key.hex(),
                "filekey": filekey,
                "rawsize": len(plain),
                "size": len(cipher),
                "file_name": os.path.basename(path),
            }

    @staticmethod
    def _build_cdn_media(uploaded: dict) -> dict:
        return {
            "encrypt_query_param": uploaded["download_param"],
            "aes_key": base64.b64encode(bytes.fromhex(uploaded["aeskey"])).decode(),
            "encrypt_type": 1,
        }

    def login(self, timeout: int = 480) -> str:
        qr_req = urllib.request.Request(
            f"{self.base_url}/ilink/bot/get_bot_qrcode?bot_type=3",
            headers=self._common_headers(),
        )
        with urllib.request.urlopen(qr_req) as r:
            qr = json.loads(r.read())

        print(f"[*] 请扫码: {qr['qrcode_img_content']}")

        deadline = time.time() + timeout
        scanned = False
        refresh = 0
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
                scanned = False
                print(f"[*] 二维码过期，刷新... ({refresh}/3)")
                with urllib.request.urlopen(qr_req) as r:
                    qr = json.loads(r.read())
                print(f"[*] 新二维码: {qr['qrcode_img_content']}")
            elif status == "confirmed":
                self.token = st.get("bot_token", "")
                if not self.token:
                    raise Exception("无 bot_token")
                self.save_session()
                print(f"[*] 登录成功: {st.get('ilink_bot_id')}")
                return self.token

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
        return self._send_items(
            to,
            [{"type": ItemType.TEXT, "text_item": {"text": text}}],
            ctx_token,
        )

    def upload_image(self, path: str, to: str) -> dict:
        return self._upload_media(path, to, MediaType.IMAGE)

    def upload_video(self, path: str, to: str) -> dict:
        return self._upload_media(path, to, MediaType.VIDEO)

    def upload_file(self, path: str, to: str) -> dict:
        return self._upload_media(path, to, MediaType.FILE)

    def send_image(self, to: str, img_info: dict, ctx_token: str = "", text: str = "") -> dict:
        items = []
        if text:
            items.append({"type": ItemType.TEXT, "text_item": {"text": text}})
        items.append(
            {
                "type": ItemType.IMAGE,
                "image_item": {
                    "media": self._build_cdn_media(img_info),
                    "mid_size": img_info["size"],
                },
            }
        )
        return self._send_items(to, items, ctx_token)

    def send_video(self, to: str, video_info: dict, ctx_token: str = "", text: str = "") -> dict:
        items = []
        if text:
            items.append({"type": ItemType.TEXT, "text_item": {"text": text}})
        items.append(
            {
                "type": ItemType.VIDEO,
                "video_item": {
                    "media": self._build_cdn_media(video_info),
                    "video_size": video_info["size"],
                },
            }
        )
        return self._send_items(to, items, ctx_token)

    def send_file(
        self,
        to: str,
        file_info: dict,
        ctx_token: str = "",
        text: str = "",
        file_name: str = "",
    ) -> dict:
        resolved_name = file_name or file_info.get("file_name") or "file.bin"
        items = []
        if text:
            items.append({"type": ItemType.TEXT, "text_item": {"text": text}})
        items.append(
            {
                "type": ItemType.FILE,
                "file_item": {
                    "media": self._build_cdn_media(file_info),
                    "file_name": resolved_name,
                    "len": str(file_info.get("rawsize", 0)),
                },
            }
        )
        return self._send_items(to, items, ctx_token)

    @staticmethod
    def get_text(msg: dict) -> str:
        parts = []
        for item in msg.get("item_list", []):
            if item.get("type") == ItemType.TEXT:
                text = item.get("text_item", {}).get("text", "")
                if text:
                    parts.append(text)
            elif item.get("type") == ItemType.VOICE:
                text = item.get("voice_item", {}).get("text", "")
                if text:
                    parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def get_media(msg: dict) -> Optional[dict]:
        for item in msg.get("item_list", []):
            if item.get("type") == ItemType.IMAGE:
                img = item.get("image_item", {})
                return {"type": "image", "url": img.get("url"), "aeskey": img.get("aeskey")}
            if item.get("type") == ItemType.FILE:
                file_item = item.get("file_item", {})
                return {
                    "type": "file",
                    "name": file_item.get("file_name"),
                    "len": file_item.get("len"),
                }
            if item.get("type") == ItemType.VIDEO:
                video = item.get("video_item", {})
                return {"type": "video", "play_length": video.get("play_length")}
        return None

    @staticmethod
    def summarize_item(item: dict) -> str:
        item_type = item.get("type")

        if item_type == ItemType.TEXT:
            text = item.get("text_item", {}).get("text", "")
            return text or "[文本]"

        if item_type == ItemType.IMAGE:
            img = item.get("image_item", {})
            size = img.get("mid_size") or img.get("hd_size") or img.get("thumb_size")
            return f"[图片 size={size}]" if size else "[图片]"

        if item_type == ItemType.VOICE:
            voice = item.get("voice_item", {})
            text = voice.get("text", "")
            if text:
                return f"[语音转文字] {text}"
            playtime = voice.get("playtime")
            return f"[语音 playtime={playtime}ms]" if playtime else "[语音]"

        if item_type == ItemType.FILE:
            file_item = item.get("file_item", {})
            name = file_item.get("file_name") or "unknown"
            length = file_item.get("len")
            return f"[文件] {name} ({length} bytes)" if length else f"[文件] {name}"

        if item_type == ItemType.VIDEO:
            video = item.get("video_item", {})
            play_length = video.get("play_length")
            return f"[视频 play_length={play_length}ms]" if play_length else "[视频]"

        return f"[未知消息类型 {item_type}]"

    @classmethod
    def build_echo_text(cls, msg: dict) -> str:
        parts = [cls.summarize_item(item) for item in msg.get("item_list", [])]
        parts = [part for part in parts if part]
        return "\n".join(parts) if parts else "[空消息]"

    def get_media_download_url(self, item: dict) -> Optional[str]:
        media = item.get("media", {})
        if media.get("full_url"):
            return media["full_url"]
        eqp = media.get("encrypt_query_param")
        if eqp:
            return f"{self.cdn_base_url}/download?encrypted_query_param={urllib.parse.quote(eqp)}"
        return None


WeixinBot = WeixinClawBot


def load_session() -> Optional[str]:
    return WeixinClawBot.load_session_token()


def save_session(token: str) -> None:
    WeixinClawBot(token=token).save_session(token)


def get_text(msg: dict) -> str:
    return WeixinClawBot.get_text(msg)


def get_media(msg: dict) -> Optional[dict]:
    return WeixinClawBot.get_media(msg)


def summarize_item(item: dict) -> str:
    return WeixinClawBot.summarize_item(item)


def build_echo_text(msg: dict) -> str:
    return WeixinClawBot.build_echo_text(msg)


def get_media_download_url(
    item: dict,
    cdn_base: str = DEFAULT_CDN_BASE_URL,
) -> Optional[str]:
    bot = WeixinClawBot(cdn_base_url=cdn_base)
    return bot.get_media_download_url(item)


def main():
    bot = WeixinClawBot.from_session()
    if bot.token:
        print("[*] 加载已有 session")
    else:
        bot.login()

    contexts = {}
    print("[*] 启动回显机器人...")

    while True:
        try:
            for msg in bot.get_updates():
                if msg.get("message_type") != MessageType.USER:
                    print(f"[wechat] {msg}")
                    continue

                user = msg["from_user_id"]
                ctx = msg.get("context_token", "")
                if ctx:
                    contexts[user] = ctx
                ctx_token = ctx or contexts.get(user, "")

                echo_text = bot.build_echo_text(msg)
                print(f"[收] {user}: {echo_text.replace(chr(10), ' | ')}")

                for item in msg.get("item_list", []):
                    if item.get("type") == ItemType.IMAGE:
                        url = bot.get_media_download_url(item.get("image_item", {}))
                    elif item.get("type") == ItemType.VOICE:
                        url = bot.get_media_download_url(item.get("voice_item", {}))
                    elif item.get("type") == ItemType.FILE:
                        url = bot.get_media_download_url(item.get("file_item", {}))
                    elif item.get("type") == ItemType.VIDEO:
                        url = bot.get_media_download_url(item.get("video_item", {}))
                    else:
                        url = None
                    if url:
                        print(f"[媒体URL] {url}")

                bot.send_text(user, echo_text, ctx_token)
                print(f"[发] {echo_text.replace(chr(10), ' | ')}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
