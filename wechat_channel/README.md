# 微信 OpenClaw 通道 Python 实现

基于 `@tencent-weixin/openclaw-weixin@2.1.8` 源码分析的纯 Python 实现，仅使用标准库 + urllib。


## 下载源码

```bash
npm view @tencent-weixin/openclaw-weixin dist.tarball
```


## 功能对照表

| 功能 | Python 实现 | 源码文件 | 状态 |
|------|------------|----------|------|
| **扫码登录** | `WeixinBot.login()` | `src/auth/login-qr.ts` | ✅ |
| **登录二维码刷新** | `login()` 内联 | `src/auth/login-qr.ts` | ✅ |
| **IDC redirect 处理** | `login()` 内联 | `src/auth/login-qr.ts` | ✅ |
| **长轮询收消息** | `WeixinBot.get_updates()` | `src/api/api.ts` | ✅ |
| **发送文本** | `WeixinBot.send_text()` | `src/messaging/send.ts` | ✅ |
| **发送图片** | `WeixinBot.send_image()` | `src/messaging/send.ts` | ✅ |
| **上传图片** | `WeixinBot.upload_image()` | `src/cdn/upload.ts` | ✅ |
| **发送视频** | - | `src/messaging/send.ts` | ❌ |
| **发送文件** | - | `src/messaging/send.ts` | ❌ |
| **上传视频/文件** | - | `src/cdn/upload.ts` | ❌ |
| **输入状态** | - | `src/api/api.ts` | ❌ |
| **获取配置** | - | `src/api/api.ts` | ❌ |
| **session 过期处理** | - | `src/api/session-guard.ts` | ❌ |
| **sync_buf 持久化** | 内存存储 | `src/storage/sync-buf.ts` | ⚠️ 简化 |


## 核心流程

### 1. 扫码登录

```
GET /ilink/bot/get_bot_qrcode?bot_type=3
  → {qrcode, qrcode_img_content}

GET /ilink/bot/get_qrcode_status?qrcode=xxx (长轮询 35s)
  → wait → scaned → scaned_but_redirect(切换host) → confirmed
  → confirmed 后获取 bot_token

二维码过期策略:
  - 最多自动刷新 3 次
```

### 2. 收消息

```
POST /ilink/bot/getupdates
请求: {get_updates_buf: "游标", base_info: {channel_version}}
响应: {ret, msgs[], get_updates_buf, longpolling_timeout_ms}

说明:
  - 长轮询超时由服务端 longpolling_timeout_ms 决定
  - 需保存 get_updates_buf 用于下次请求
```

### 3. 发消息

```
POST /ilink/bot/sendmessage
{
  msg: {
    to_user_id: "xxx@im.wechat",
    client_id: "py:时间戳-随机hex",
    message_type: MessageType.BOT,
    message_state: MessageState.FINISH,
    item_list: [{type: ItemType.TEXT, text_item: {text: "内容"}}],
    context_token: "从收到的消息获取(可选)"
  }
}
```

### 4. 上传图片

```
POST /ilink/bot/getuploadurl
  → {upload_full_url} 或 {upload_param}

AES-128-ECB + PKCS7 加密文件

POST https://novac2c.cdn.weixin.qq.com/c2c/upload
  → 响应头 x-encrypted-param 即 download_param
```


## 枚举定义

```python
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
```


## 请求头

```python
{
    "Content-Type": "application/json",
    "AuthorizationType": "ilink_bot_token",
    "Authorization": f"Bearer {token}",
    "X-WECHAT-UIN": "随机uint32→十进制→base64",
    "iLink-App-Id": "bot",
    "iLink-App-ClientVersion": "67336",  # 2.1.8
}
```


## 使用示例

```python
from demo import WeixinBot, MessageType, ItemType, get_text, get_media, summarize_item, build_echo_text

# 扫码登录
bot = WeixinBot()
token = bot.login()

# 使用已有 token
bot = WeixinBot("your_token_here")

# 收消息
for msg in bot.get_updates():
    if msg.get("message_type") != MessageType.USER:
        continue
    user = msg["from_user_id"]
    ctx_token = msg.get("context_token", "")

    # 提取文本
    text = get_text(msg)

    # 提取媒体
    media = get_media(msg)

    # 生成回显文本
    echo = build_echo_text(msg)

    # 发送文本
    bot.send_text(user, echo, ctx_token)

    # 发送图片
    img = bot.upload_image("/path/to/image.jpg", user)
    bot.send_image(user, img, ctx_token)
```


## 依赖

- Python 3.7+
- 加密库（二选一）:
  - `pycryptodome`: `pip install pycryptodome`
  - `cryptography`: `pip install cryptography`
