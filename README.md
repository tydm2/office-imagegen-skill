# office-imagegen —— 办公文档 AI 生图技能

给 **PPT / Word / Excel** 生成插图并一键嵌入的 Agent 技能（SKILL.md + 零依赖 CLI）。多后端兼容，免费后端开箱即用，专为办公文档版式优化。

> English: An agent skill for generating & embedding images in office documents (PPT/Word/Excel). Multi-backend (free Pollinations / OpenAI / Gemini Nano Banana), text-to-image + image-to-image + inpainting, one-command embed into `.pptx` / `.docx`.

## 为什么做这个（创新点）

现有生图技能多为「单一后端 + 通用出图」，本技能针对**办公文档场景**做了三层增强：

1. **多后端统一接口**：一个命令切换 `pollinations`（免费免密钥）/ `openai`（DALL·E/gpt-image）/ `gemini`（Nano Banana），免费优先、按需升级。
2. **办公版式预设**：`title`(封面) / `divider`(章节) / `content`(配图) / `square`(logo) / `banner`(页眉条) / `portrait`(竖版)，自动换算到各后端合法尺寸，对齐 PPT/Word 版式。
3. **一键嵌入**：生成后直接嵌入 `.pptx` 指定页 / `.docx` 指定位置，无需手工插图。
4. **办公提示词库**：封面/章节/配图/图标/背景模板 + 避坑（图中乱字、版权、比例、配色一致性）。

## 安装

把本目录放进任意技能根（本技能目录名须为 `office-imagegen`）：

- 项目级：`<workspace>/.dsh/skills/office-imagegen/`
- 用户级：`~/.dsh/skills/office-imagegen/`
- 其他 agent：`~/.claude/skills/office-imagegen/`、`~/.agents/skills/office-imagegen/` 等

## 用法

```powershell
# 文生图：16:9 封面（免费，免密钥）
python scripts/imagegen.py generate --backend pollinations --layout title --prompt "科技公司年度战略汇报封面，深蓝渐变背景，抽象几何线条，简洁高级，无文字" --out cover.png

# 图生图：改扁平插画风格（需 OPENAI_API_KEY）
python scripts/imagegen.py generate --backend openai --layout square --image src.png --prompt "改成扁平插画风格" --out out.png

# 一键嵌入：PPT 第 1 页 / Word 居中
python scripts/imagegen.py embed --images cover.png --target 汇报.pptx --slide 1
python scripts/imagegen.py embed --images cover.png --target 报告.docx --position center

# 看版式预设
python scripts/imagegen.py layouts
```

## 依赖

- **生成**：零第三方依赖（标准库 `urllib`）。
- **嵌入**：`pip install pillow python-docx python-pptx`（按需）。

## 密钥

| 后端 | 环境变量 | 获取 |
|---|---|---|
| pollinations | 无（免费文生图） | — |
| openai | `OPENAI_API_KEY` | platform.openai.com/api-keys |
| gemini | `GEMINI_API_KEY` | aistudio.google.com/apikey |

密钥只走环境变量，绝不写进脚本/日志/提交。

## 目录结构

```
office-imagegen/
├── SKILL.md                     # 技能主契约（触发条件 + 核心步骤）
├── scripts/
│   └── imagegen.py              # 生成 + 嵌入 CLI（stdlib）
├── references/
│   ├── backends.md              # 各后端 API / 尺寸映射 / 密钥
│   └── prompt-library.md        # 办公提示词库 + 避坑
└── README.md
```

## 安全与合规

- API key 仅经环境变量注入，不回显、不打印、不提交。
- 提示词规避在世风格/在世人物/商标与受版权风格；商用前确认素材授权。
- 生成结果先预览再定稿，避免「AI 幻觉文字」进入正式文档。
