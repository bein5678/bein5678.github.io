"""Hugo 사이트에 포스트 추가 + GitHub 푸시"""
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

_REPO = Path.home() / "gallery"


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9가-힣\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:60] or "post"


def publish(korean_keyword: str, english_prompt: str, image_path: str,
            character: str = "", dialogue: str = "", tip: str = "") -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    slug_src = " ".join(english_prompt.split()[:6])
    slug = f"{today}-{_slugify(slug_src)}"

    folder = _REPO / "content" / slug
    folder.mkdir(parents=True, exist_ok=True)

    img_dst = folder / "cover.png"
    shutil.copy(image_path, img_dst)

    title = character if character else korean_keyword

    body_parts = []
    if character:
        body_parts.append("## 🎭 캐릭터\n\n**" + character + "**\n")
    if dialogue:
        body_parts.append("## 💬 대사\n\n> " + dialogue + "\n")
    if tip:
        body_parts.append("## 💡 꿀팁\n\n" + tip + "\n")
    if not body_parts:
        body_parts.append(korean_keyword + "\n")

    body = "\n".join(body_parts)

    front_matter = (
        "---\n"
        f'title: "{title}"\n'
        f"date: {datetime.now().isoformat()}\n"
        "draft: false\n"
        "cover:\n"
        "  image: cover.png\n"
        f'  alt: "{title}"\n'
        "---\n\n"
    )

    md = front_matter + body

    (folder / "index.md").write_text(md, encoding="utf-8")

    subprocess.run(["git", "-C", str(_REPO), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(_REPO), "commit", "-m", f"add post: {slug}"],
        check=True,
    )
    subprocess.run(["git", "-C", str(_REPO), "push", "origin", "main"], check=True)

    base_url = os.environ.get("SITE_BASE_URL", "https://bein5678.github.io").rstrip("/")
    return f"{base_url}/{slug}/"
