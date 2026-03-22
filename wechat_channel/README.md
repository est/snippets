# 微信 OpenClaw 通道 Python 实现

基于 `@tencent-weixin/openclaw-weixin@1.0.2` 源码分析的纯 Python 实现，仅使用标准库 + urllib。

## 功能对照表

| 功能 | Python 实现 | 源码文件 | 状态 |
|------|------------|----------|------|
| **扫码登录** | `WeixinBot.login()` | `src/auth/login-qr.ts` | ✅ 已实现 |
| **长轮询收消息** | `WeixinBot.get_updates()` | `src/api/api.ts:130-162` | ✅ 已实现 |
| **发送文本** | `WeixinBot.send_text()` | `src/messaging/send.ts:70-95` | ✅ 已实现 |
| **发送图片** | `WeixinBot.send_image()` | `src/messaging/send.ts:140-170` | ✅ 已实现 |
| **发送视频** | - | `src/messaging/send.ts:172-200` | ❌ 未实现 |
| **发送文件** | - | `src/messaging/send.ts:202-230` | ❌ 未实现 |
| **上传图片** | `WeixinBot.upload_image()` | `src/cdn/upload.ts:108-120` | ✅ 已实现 |
| **上传视频** | - | `src/cdn/upload.ts:122-134` | ❌ 未实现 |
| **上传文件** | - | `src/cdn/upload.ts:136-155` | ❌ 未实现 |
| **输入状态** | - | `src/api/api.ts:214-224` | ❌ 未实现 |
| **获取配置** | - | `src/api/api.ts:196-212` | ❌ 未实现 |
| **语音消息** | `get_text()` 支持提取 | `src/messaging/inbound.ts:96-100` | ✅ 部分实现 |
| **引用消息** | - | `src/messaging/inbound.ts:78-94` | ❌ 未实现 |
| **Markdown 转纯文本** | - | `src/messaging/send.ts:23-38` | ❌ 未实现 |
| **session 过期处理** | - | `src/api/session-guard.ts` | ❌ 未实现 |
| **sync_buf 持久化** | 内存存储 | `src/storage/sync-buf.ts` | ⚠️ 简化实现 |
| **多账号管理** | - | `src/auth/accounts.ts` | ❌ 未实现 |
| **远程图片下载** | - | `src/cdn/upload.ts:27-47` | ❌ 未实现 |
| **图片解密** | - | `src/cdn/pic-decrypt.ts` | ❌ 未实现 |
| **语音转码 (silk)** | - | `src/media/silk-transcode.ts` | ❌ 未实现 |

## 核心流程

### 1. 扫码登录 (src/auth/login-qr.ts)

```
GET /ilink/bot/get_bot_qrcode?bot_type=3
  → {qrcode, qrcode_img_content}

GET /ilink/bot/get_qrcode_status?qrcode=xxx (长轮询)
  → 状态: wait → scaned → confirmed
  → confirmed 后获取 bot_token
```

### 2. 收消息 (src/api/api.ts:130-162)

```python
POST /ilink/bot/getupdates
请求: {get_updates_buf: "游标"}
响应: {ret, msgs[], get_updates_buf}

- 长轮询 35s 超时是正常的
- 需保存 get_updates_buf 用于下次请求
```

### 3. 发消息 (src/messaging/send.ts)

```python
POST /ilink/bot/sendmessage
{
  msg: {
    to_user_id: "xxx@im.wechat",
    client_id: "唯一ID",
    message_type: 2,  # BOT
    message_state: 2,  # FINISH
    item_list: [...],
    context_token: "必须从收的消息获取"
  }
}
```

**关键**: `context_token` 是必须的，从收到的消息中复制。

### 4. 上传媒体 (src/cdn/upload.ts, src/cdn/cdn-upload.ts)

```python
# 步骤1: 获取上传 URL
POST /ilink/bot/getuploadurl
→ {upload_param}

# 步骤2: AES-128-ECB 加密文件

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

## 默认配置 (src/auth/accounts.ts:13-14)

```python
base_url = "https://ilinkai.weixin.qq.com"
cdn_base_url = "https://novac2c.cdn.weixin.qq.com/c2c"
```

## 使用方法

```python
from demo import WeixinBot

# 扫码登录
bot = WeixinBot()
token = bot.login()  # 会打印二维码链接，扫码后返回 token

# 使用已有 token
bot = WeixinBot("your_token_here")

# 收消息
for msg in bot.get_updates():
    print(msg)

# 发消息（需要 context_token）
bot.send_text("user@im.wechat", "Hello", context_token)

# 发图片
img_info = bot.upload_image("/path/to/image.jpg", "user@im.wechat")
bot.send_image("user@im.wechat", img_info, context_token)
```

## 依赖

- Python 3.7+
- 加密库（二选一）:
  - `pycryptodome`: `pip install pycryptodome`
  - `cryptography`: `pip install cryptography`

## 缺失功能说明

以下功能在源码中存在但 Python 实现中未包含：

1. **视频/文件发送** - 类似图片，只是 media_type 不同
2. **输入状态指示器** - 打字/取消打字状态
3. **语音消息处理** - silk 格式转码
4. **引用消息解析** - 回复时引用原消息
5. **Markdown 转纯文本** - 清理格式后发送
6. **Session 过期处理** - errcode -14 时暂停重试
7. **多账号管理** - 同时登录多个微信账号
