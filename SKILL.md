---
name: office-imagegen
description: 当用户需要在办公文档（PPT/Word/Excel）中配图或生成插图——封面、章节页、内容配图、图标、背景、页眉条——时使用；也用于把生成的图片一键嵌入 .pptx/.docx。多后端兼容（免费 Pollinations 免密钥、OpenAI DALL·E/gpt-image、Gemini Nano Banana），支持文生图/图生图/局部重绘，产出可直接嵌入文档的图片文件。不用于生成视频、音频，也不用于纯文字排版（那是文档编辑本身）。
metadata:
  version: 1.0.0
  languages: [zh, en]
  changelog:
    - 1.0.0: 初始版本——多后端生图 + 办公布局预设 + 一键嵌入文档
---

# office-imagegen —— 办公文档 AI 生图

给办公文档（PPT / Word / Excel）生成插图并一键嵌入：封面、章节页、内容配图、图标、背景、页眉条。多后端兼容，免费后端开箱即用。

## 何时用 / 何时不用

- **用**：给 .pptx/.docx 生成封面图、章节页、配图、图标、背景、页眉条；对已有图片改风格（图生图）或局部重绘；生成后直接嵌入文档指定位置。
- **不用**：生成视频、音频、3D；纯文字排版与图表数据（那是文档编辑本身）；已有现成素材且无需 AI 生成。

## 快速开始（三步）

1. **定后端与版式**：默认 `pollinations`（免费、免密钥）。看版式预设：
   `python scripts/imagegen.py layouts`
2. **写提示词**：按 `references/prompt-library.md` 的办公提示词库润色（含 **style_id→绘图风格映射表**，可与 office-studio 风格库联动：文档定了风格后按映射取生图风格句，保证图文统一），规避「图中乱字」与版权风险。
3. **生成 + 嵌入**：

```powershell
# 文生图：16:9 封面（免费后端）
python scripts/imagegen.py generate --backend pollinations --layout title --prompt "科技公司年度战略汇报封面，深蓝渐变背景，抽象几何线条，简洁高级" --out cover.png

# 图生图：改扁平插画风格（openai，需 OPENAI_API_KEY）
python scripts/imagegen.py generate --backend openai --layout square --image src.png --prompt "改成扁平插画风格" --out out.png

# 一键嵌入：PPT 第 1 页 / Word 末尾
python scripts/imagegen.py embed --images cover.png --target 汇报.pptx --slide 1
python scripts/imagegen.py embed --images cover.png --target 报告.docx --position center
```

## 后端选择

| 后端 | 密钥 | 文生图 | 图生图/重绘 | 说明 |
|---|---|---|---|---|
| `pollinations` | 无 | ✅ | 需新 API/密钥 | 免费、开箱即用，默认 |
| `openai` | `OPENAI_API_KEY` | ✅ | ✅ | gpt-image-1 / dall-e-3，质量最高 |
| `gemini` | `GEMINI_API_KEY` | ✅ | ✅ | gemini-2.5-flash-image（Nano Banana） |

- 密钥只经**环境变量**注入，绝不写进对话、脚本、日志或提交；生成失败按「换后端 → 降尺寸 → 重试」顺序处理。
- 各后端精确 API、尺寸映射、图生图/局部重绘细节见 `references/backends.md`。

## 版式预设（对齐办公版式）

`title`(16:9 封面) · `divider`(章节页) · `content`(16:9 配图) · `square`(方图/logo) · `banner`(页眉横条) · `portrait`(竖版)。各后端自动换算到最接近的合法尺寸；也可用 `--size WxH` 覆盖。

## 脚本用法

- 生成：`python scripts/imagegen.py generate --backend <b> --layout <L>|--size WxH --prompt <P> [--image <src>] [--mask <m>] [--seed N] --out <file>`
- 嵌入：`python scripts/imagegen.py embed --images <f1> [f2 …] --target <docx|pptx> [--slide N] [--position left|center|right] [--width-cm W]`
- 依赖：生成本身零第三方依赖（标准库 urllib）；嵌入需 `pip install pillow python-docx python-pptx`（缺哪个装哪个）。

## 安全与合规

- API key 仅环境变量注入，不回显、不打印、不提交。
- 提示词规避在世风格/在世人物/商标与受版权风格（详见 `references/prompt-library.md`）；商用前确认素材授权。
- 生成结果先预览再定稿，避免「AI 幻觉文字」进入正式文档。
