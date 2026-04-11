# 微信 OpenClaw 通道 Python 实现

基于 `@tencent-weixin/openclaw-weixin@2.1.7` 源码分析的纯 Python 实现，仅使用标准库 + urllib。


## 下载源码

```bash
npm view @tencent-weixin/openclaw-weixin dist.tarball
```


## 功能对照表

| 功能 | Python 实现 | 源码文件 | 状态 |
|------|------------|----------|------|
| **扫码登录** | `WeixinBot.login()` | `src/auth/login-qr.ts` | ✅ 已实现 |
| **登录二维码刷新** | `login()` 内联 | `src/auth/login-qr.ts` | ✅ 已实现 |
| **IDC redirect 处理** | `login()` 内联 | `src/auth/login-qr.ts` | ✅ 已实现 |
| **长轮询收消息** | `WeixinBot.get_updates()` | `src/api/api.ts` | ✅ 已实现 |
| **发送文本** | `WeixinBot.send_text()` | `src/messaging/send.ts` | ✅ 已实现 |
| **发送图片** | `WeixinBot.send_image()` | `src/messaging/send.ts` | ✅ 已实现 |
| **发送视频** | - | `src/messaging/send.ts` | ❌ 未实现 |
| **发送文件** | - | `src/messaging/send.ts` | ❌ 未实现 |
| **上传图片** | `WeixinBot.upload_image()` | `src/cdn/upload.ts` | ✅ 已实现 |
| **上传视频** | - | `src/cdn/upload.ts` | ❌ 未实现 |
| **上传文件** | - | `src/cdn/upload.ts` | ❌ 未实现 |
| **输入状态** | - | `src/api/api.ts` | ❌ 未实现 |
| **获取配置** | - | `src/api/api.ts` | ❌ 未实现 |
| **语音消息** | `get_text()` 提取 | `src/messaging/inbound.ts` | ✅ 部分实现 |
| **媒体消息解析** | `get_media()` | `src/api/types.ts` | ✅ 部分实现 |
| **引用消息** | - | `src/messaging/inbound.ts` | ❌ 未实现 |
| **Markdown 转纯文本** | - | `src/messaging/markdown-filter.ts` | ❌ 未实现 |
| **session 过期处理** | - | `src/api/session-guard.ts` | ❌ 未实现 |
| **sync_buf 持久化** | 内存存储 | `src/storage/sync-buf.ts` | ⚠️ 简化实现 |
| **多账号管理** | - | `src/auth/accounts.ts` | ❌ 未实现 |
| **远程图片下载** | - | `src/cdn/upload.ts` | ❌ 未实现 |
| **图片解密** | - | `src/cdn/pic-decrypt.ts` | ❌ 未实现 |
| **语音转码 (silk)** | - | `src/media/silk-transcode.ts` | ❌ 未实现 |


## 核心流程

### 1. 扫码登录 (src/auth/login-qr.ts)

```
GET /ilink/bot/get_bot_qrcode?bot_type=3
  → {qrcode, qrcode_img_content}

GET /ilink/bot/get_qrcode_status?qrcode=xxx (长轮询 35s)
  → 状态: wait → scaned → scaned_but_redirect(切换host) → confirmed
  → confirmed 后获取 bot_token

二维码过期策略:
  - 最多自动刷新 3 次
  - 每次刷新后需重新扫码
```

### 2. 收消息 (src/api/api.ts)

```
POST /ilink/bot/getupdates
请求: {get_updates_buf: "游标", base_info: {channel_version}}
响应: {ret, msgs[], get_updates_buf, longpolling_timeout_ms}

说明:
  - 长轮询 35s 超时是正常的
  - 需保存 get_updates_buf 用于下次请求
  - message_type=1 为用户消息, message_state=0 为新消息
```

### 3. 发消息 (src/messaging/send.ts)

```
POST /ilink/bot/sendmessage
{
  msg: {
    to_user_id: "xxx@im.wechat",
    client_id: "py:时间戳-随机hex",
    message_type: 2,  # BOT
    message_state: 2,  # FINISH
    item_list: [{type: 1, text_item: {text: "内容"}}],
    context_token: "从收到的消息复制"
  }
}

context_token 是可选的，但建议填写以确保会话关联
```

### 4. 上传图片 (src/cdn/upload.ts, src/cdn/cdn-upload.ts)

```
# 步骤1: 获取上传 URL
POST /ilink/bot/getuploadurl
  → {upload_full_url} 或 {upload_param}

# 步骤2: AES-128-ECB + PKCS7 加密文件

# 步骤3: 上传到 CDN
POST https://novac2c.cdn.weixin.qq.com/c2c/upload
  → 从响应头 x-encrypted-param 获取 download_param
```


## 常量定义 (src/api/types.ts)

```python
# UploadMediaType
IMAGE = 1
VIDEO = 2
FILE = 3
VOICE = 4

# MessageType
USER = 1
BOT = 2

# MessageState
NEW = 0
GENERATING = 1
FINISH = 2

# MessageItemType
TEXT = 1
IMAGE = 2
VOICE = 3
FILE = 4
VIDEO = 5
```


## 请求头

```python
{
    "Content-Type": "application/json",
    "AuthorizationType": "ilink_bot_token",
    "Authorization": f"Bearer {token}",
    "X-WECHAT-UIN": "随机uint32→十进制→base64",
    "iLink-App-Id": "com.tencent.wechat.openclaw",
    "iLink-App-ClientVersion": "65547",  # 1.0.11
}
```


## 默认配置

```python
base_url = "https://ilinkai.weixin.qq.com"
cdn_base_url = "https://novac2c.cdn.weixin.qq.com/c2c"
```


## 使用示例

```python
from demo import WeixinBot, get_text, get_media

# 扫码登录
bot = WeixinBot()
token = bot.login()  # 打印二维码，扫码后返回 token

# 使用已有 token
bot = WeixinBot("your_token_here")

# 收消息
for msg in bot.get_updates():
    user = msg["from_user_id"]
    text = get_text(msg)
    media = get_media(msg)

# 发文本
bot.send_text("user@im.wechat", "Hello", ctx_token)

# 发图片
img = bot.upload_image("/path/to/image.jpg", "user@im.wechat")
bot.send_image("user@im.wechat", img, ctx_token)
```


## 依赖

- Python 3.7+
- 加密库（二选一）:
  - `pycryptodome`: `pip install pycryptodome`
  - `cryptography`: `pip install cryptography`
