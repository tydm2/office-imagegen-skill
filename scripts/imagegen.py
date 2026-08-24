#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
office-imagegen —— 办公文档 AI 生图 CLI（多后端 + 一键嵌入）

后端：
  pollinations  免费、免密钥（文生图；图生图需新 API/密钥）
  openai        OPENAI_API_KEY（文生图 gpt-image-1/dall-e-3；图生图/局部重绘 images/edits）
  gemini        GEMINI_API_KEY（gemini-2.5-flash-image "Nano Banana"，文生图/图生图）

依赖：
  - 生成本身零第三方依赖（标准库 urllib + json）。
  - 嵌入：docx 需 python-docx；pptx 需 python-pptx；宽度换算可用 pillow（非必需）。

示例：
  python imagegen.py generate --backend pollinations --layout title --prompt "..." --out cover.png
  python imagegen.py generate --backend openai --layout square --image in.png --prompt "改扁平风格" --out out.png
  python imagegen.py embed --images cover.png --target deck.pptx --slide 1
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# 版式预设：办公文档版式 -> pollinations 尺寸 / openai 合法尺寸 / gemini 宽高比
LAYOUTS = {
    "title":    {"w": 1920, "h": 1080, "openai": "1536x1024", "aspect": "16:9",  "use": "PPT 封面"},
    "divider":  {"w": 1920, "h": 1080, "openai": "1536x1024", "aspect": "16:9",  "use": "章节页/过渡页"},
    "content":  {"w": 1280, "h": 720,  "openai": "1536x1024", "aspect": "16:9",  "use": "正文内容配图"},
    "square":   {"w": 1024, "h": 1024, "openai": "1024x1024", "aspect": "1:1",   "use": "Word 插图/logo/头像"},
    "banner":   {"w": 1536, "h": 512,  "openai": "1536x1024", "aspect": "3:1",   "use": "页眉横条/PPT 底部横幅"},
    "portrait": {"w": 1080, "h": 1920, "openai": "1024x1536", "aspect": "9:16",  "use": "竖版图/Word 侧边"},
}

POLLINATIONS_MODELS = ["flux", "turbo"]
OPENAI_MODELS = ["gpt-image-1", "dall-e-3"]
GEMINI_MODELS = ["gemini-2.5-flash-image"]


# ---------- 网络基础 ----------
def http_get(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "office-imagegen/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_post_json(url, payload, headers=None, timeout=300):
    data = json.dumps(payload).encode("utf-8")
    h = {"Content-Type": "application/json", "User-Agent": "office-imagegen/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_post_bytes(url, body, headers, timeout=300):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save(data, out):
    with open(out, "wb") as f:
        f.write(data)
    return len(data)


# ---------- 各后端实现 ----------
def gen_pollinations(prompt, w, h, model, seed, out):
    q = urllib.parse.quote(prompt)
    params = f"width={w}&height={h}&model={model}&nologo=true"
    if seed is not None:
        params += f"&seed={seed}"
    url = POLLINATIONS_URL.format(prompt=q) + "?" + params
    return save(http_get(url), out)


def gen_openai(prompt, size, model, seed, out, image=None, mask=None):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("缺少 OPENAI_API_KEY（请先设置环境变量）")
    headers = {"Authorization": f"Bearer {key}"}
    if image is not None:
        # 图生图 / 局部重绘：multipart images/edits
        import uuid
        boundary = uuid.uuid4().hex
        fields = {"model": model, "prompt": prompt, "size": size, "n": "1"}
        files = {"image": (os.path.basename(image), _read(image), "image/png")}
        if mask is not None:
            files["mask"] = (os.path.basename(mask), _read(mask), "image/png")
        body = b""
        for k, v in fields.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, (fn, data, ct) in files.items():
            body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; '
                     f'filename="{fn}"\r\nContent-Type: {ct}\r\n\r\n').encode() + data + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        resp = http_post_bytes(f"{OPENAI_BASE}/images/edits", body,
                               {**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        resp = http_post_json(f"{OPENAI_BASE}/images/generations",
                              {"model": model, "prompt": prompt, "size": size, "n": 1}, headers)
    j = json.loads(resp)
    item = j["data"][0]
    if item.get("b64_json"):
        data = base64.b64decode(item["b64_json"])
    elif item.get("url"):
        data = http_get(item["url"])
    else:
        sys.exit(f"OpenAI 响应无图片数据：{json.dumps(j, ensure_ascii=False)[:200]}")
    return save(data, out)


def gen_gemini(prompt, aspect, model, out, image=None):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("缺少 GEMINI_API_KEY（请先设置环境变量）")
    url = f"{GEMINI_BASE}/models/{model}:generateContent?key={key}"
    parts = [{"text": prompt}]
    if image is not None:
        b64 = base64.b64encode(_read(image)).decode()
        parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    if aspect:
        payload["generationConfig"]["imageConfig"] = {"aspectRatio": aspect}
    j = json.loads(http_post_json(url, payload))
    for part in j["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return save(base64.b64decode(part["inlineData"]["data"]), out)
    sys.exit(f"Gemini 响应无图片：{json.dumps(j, ensure_ascii=False)[:200]}")


def _read(path):
    with open(path, "rb") as f:
        return f.read()


# ---------- 命令实现 ----------
def cmd_generate(args):
    if args.layout:
        L = LAYOUTS[args.layout]
        w, h, openai_size, aspect = L["w"], L["h"], L["openai"], L["aspect"]
    elif args.size:
        w, h = [int(x) for x in args.size.lower().split("x")]
        openai_size = f"{w}x{h}"
        aspect = None
    else:
        w, h, openai_size, aspect = 1024, 1024, "1024x1024", "1:1"

    if args.backend == "pollinations":
        if args.image:
            sys.exit("pollinations 免费 URL 端点仅支持文生图；图生图请用 --backend openai/gemini，"
                     "或给 pollinations 配置 API key（见 references/backends.md）")
        n = gen_pollinations(args.prompt, w, h, args.model or "flux", args.seed, args.out)
    elif args.backend == "openai":
        n = gen_openai(args.prompt, openai_size, args.model or "gpt-image-1", args.seed,
                       args.out, args.image, args.mask)
    elif args.backend == "gemini":
        n = gen_gemini(args.prompt, aspect, args.model or "gemini-2.5-flash-image",
                       args.out, args.image)
    else:
        sys.exit(f"未知后端：{args.backend}")
    print(f"OK {args.out}（{n} bytes，backend={args.backend}）")


def cmd_embed(args):
    ext = os.path.splitext(args.target)[1].lower()
    if ext == ".docx":
        try:
            import docx
        except ImportError:
            sys.exit("需要 python-docx：pip install python-docx")
        w = _width(args)
        d = docx.Document(args.target)
        for img in args.images:
            if args.position == "center":
                p = d.add_paragraph()
                p.alignment = 1  # WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(img, width=w)
            else:
                d.add_picture(img, width=w)
        d.save(args.target)
    elif ext == ".pptx":
        try:
            from pptx import Presentation
        except ImportError:
            sys.exit("需要 python-pptx：pip install python-pptx")
        from pptx.util import Cm
        w = Cm(args.width_cm or 16)
        prs = Presentation(args.target)
        if args.slide < 1 or args.slide > len(prs.slides):
            sys.exit(f"PPT 页码越界：共 {len(prs.slides)} 页，给了 {args.slide}")
        slide = prs.slides[args.slide - 1]
        for img in args.images:
            slide.shapes.add_picture(img, Cm(3), Cm(3), width=w)
        prs.save(args.target)
    else:
        sys.exit(f"不支持的目标格式：{ext}（仅 .docx / .pptx）")
    print(f"OK 已嵌入 {len(args.images)} 张图到 {args.target}")


def _width(args):
    if not args.width_cm:
        return None
    try:
        from docx.shared import Cm
        return Cm(args.width_cm)
    except ImportError:
        return None


def cmd_layouts(_args):
    for k, v in LAYOUTS.items():
        print(f"{k:10s} {v['aspect']:6s} {v['w']}x{v['h']}  {v['use']}")


def main():
    ap = argparse.ArgumentParser(description="办公文档 AI 生图 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="生成图片")
    g.add_argument("--backend", choices=["pollinations", "openai", "gemini"], default="pollinations")
    g.add_argument("--layout", choices=list(LAYOUTS))
    g.add_argument("--size", help="WxH，如 1024x1024（与 --layout 二选一）")
    g.add_argument("--model")
    g.add_argument("--prompt", required=True)
    g.add_argument("--image", help="图生图/局部重绘的输入图（png/jpg）")
    g.add_argument("--mask", help="局部重绘蒙版（透明 PNG，仅 openai）")
    g.add_argument("--seed", type=int)
    g.add_argument("--out", required=True)
    g.set_defaults(func=cmd_generate)

    e = sub.add_parser("embed", help="嵌入图片到文档")
    e.add_argument("--images", nargs="+", required=True)
    e.add_argument("--target", required=True, help=".docx / .pptx")
    e.add_argument("--slide", type=int, default=1, help="PPT 页码（默认 1）")
    e.add_argument("--position", choices=["left", "center", "right"], default="left")
    e.add_argument("--width-cm", type=float, help="图片宽度（厘米，默认自适应）")
    e.set_defaults(func=cmd_embed)

    l = sub.add_parser("layouts", help="列出版式预设")
    l.set_defaults(func=cmd_layouts)

    args = ap.parse_args()
    try:
        args.func(args)
    except urllib.error.URLError as err:
        sys.exit(f"网络错误：{err}。请检查网络/代理，或换后端重试。")
    except KeyError as err:
        sys.exit(f"响应结构异常（缺字段 {err}），可能是后端接口变更，请对照 references/backends.md。")


if __name__ == "__main__":
    main()
