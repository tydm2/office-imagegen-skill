# 后端参考（backends）

各后端的精确 API、密钥配置、尺寸映射、图生图/局部重绘细节。生成前先确认后端与密钥。

## 通用铁律

- **密钥只走环境变量**，绝不写进脚本、对话、日志、提交。
  - PowerShell：`$env:OPENAI_API_KEY="sk-..."; $env:GEMINI_API_KEY="AIza..."`
  - 用完可 `Remove-Item Env:OPENAI_API_KEY` 清理。
- 生成失败处理顺序：**换后端 → 降尺寸/降质量 → 指数退避重试（1s→2s→4s）**。
- 输出文件写本地 `--out`，不把图片字节回显到终端。

## 1. pollinations（免费，默认）

- **文生图（免费、免密钥）**：经典 URL 端点
  `GET https://image.pollinations.ai/prompt/{URL编码提示词}?width=W&height=H&model=flux&nologo=true&seed=N`
  - 模型：`flux`（默认，质量最高）、`turbo`（更快）。
  - 常见尺寸：1024x1024、1920x1080、1280x720、1080x1920、1536x512。
  - `nologo=true` 去水印；`seed` 固定可复现；可加 `enhance=true` 增强。
- **图生图**：免费 URL 端点仅文生图。图生图走新版 OpenAI 兼容接口
  `POST https://gen.pollinations.ai/v1/images/generations`，body 含 `image`（参考图 URL）与 `model`，需 API key。
  → 本脚本图生图请直接选 `--backend openai` 或 `--backend gemini`。

## 2. openai（需 OPENAI_API_KEY）

- **文生图**：`POST {OPENAI_BASE}/images/generations`
  body：`{"model":"gpt-image-1","prompt":"...","size":"...","n":1}`
  - 模型：`gpt-image-1`（默认，支持编辑）、`dall-e-3`（经典高质量）。
  - 尺寸：gpt-image-1 = 1024x1024 / 1536x1024 / 1024x1536；dall-e-3 = 1024x1024 / 1792x1024 / 1024x1792。
  - 响应：`data[0].b64_json`（gpt-image-1 默认）或 `data[0].url`。
- **图生图 / 局部重绘**：`POST {OPENAI_BASE}/images/edits`（multipart）
  - 字段：`model`、`image`（输入图）、`mask`（可选，透明 PNG，非透明区域=要重绘）、`prompt`、`size`、`n`。
  - `--image src.png` 做图生图；`--image src.png --mask mask.png` 做局部重绘。
- 兼容网关：设置 `OPENAI_BASE_URL` 可指向任意 OpenAI 兼容服务。

## 3. gemini（需 GEMINI_API_KEY，Nano Banana）

- 模型：`gemini-2.5-flash-image`（Nano Banana Pro）；旧版 `gemini-2.0-flash-preview-image-generation`。
- **文生图 / 图生图同一入口**：`POST {GEMINI_BASE}/models/{model}:generateContent?key=KEY`
  body：`{"contents":[{"parts":[{"text":"..."},{"inline_data":{"mime_type":"image/png","data":"<base64>"}}]}],"generationConfig":{"responseModalities":["IMAGE","TEXT"]}}`
  - 图生图：把输入图作为 `inline_data` 一起放进 parts。
  - 宽高比：`generationConfig.imageConfig.aspectRatio`（如 "16:9"、"3:1"、"9:16"）。
  - 响应：`candidates[0].content.parts[].inlineData.data`（base64）。
- 优点：图生图/多轮编辑能力强，适合「把这张图改成 XX 风格」类需求。

## 版式 → 尺寸映射

| 版式 | 用途 | pollinations | openai(gpt-image-1) | gemini aspect |
|---|---|---|---|---|
| title | PPT 封面 | 1920x1080 | 1536x1024 | 16:9 |
| divider | 章节页 | 1920x1080 | 1536x1024 | 16:9 |
| content | 正文配图 | 1280x720 | 1536x1024 | 16:9 |
| square | 插图/logo | 1024x1024 | 1024x1024 | 1:1 |
| banner | 页眉横条 | 1536x512 | 1536x1024* | 3:1 |
| portrait | 竖版 | 1080x1920 | 1024x1536 | 9:16 |

\* openai 不支持 3:1，自动退到最接近的 1536x1024（3:2），banner 若需精确 3:1 请用 pollinations 或 gemini。

## 密钥获取

- OpenAI：https://platform.openai.com/api-keys
- Gemini：https://aistudio.google.com/apikey
- pollinations 免密钥（免费文生图）；进阶 API key 见 https://pollinations.ai
