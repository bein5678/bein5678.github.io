"""생성된 이미지를 Hugo content/ 폴더에 배치하고 git push 한다."""
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parent
_CONTENT = _REPO_ROOT / "content"
_USER = os.getenv("GITHUB_USERNAME", "bein5678")
_PAT = os.getenv("GITHUB_PAT")
_REPO = os.getenv("GITHUB_REPO", "bein5678/bein5678.github.io")
_SITE = os.getenv("SITE_URL", "https://bein5678.github.io").rstrip("/")

def _slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    return text[:40] or "post"

def publish(korean_keyword: str, english_prompt: str, image_bytes_path: Path) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    slug = f"{today}-{_slugify(' '.join(english_prompt.split()[:6]))}"
    post_dir = _CONTENT / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    img_dest = post_dir / "image.png"
    img_dest.write_bytes(Path(image_bytes_path).read_bytes())
    safe_kw = korean_keyword.replace('"', "'")
    safe_prompt = english_prompt.replace('"', "'").replace("\n", " ")
    (post_dir / "index.md").write_text(
        f'---\ntitle: "{safe_kw}"\ndate: {datetime.now().isoformat()}\ndraft: false\n'
        f'description: "{safe_prompt[:160]}"\n---\n\n![{safe_kw}](image.png)\n',
        encoding="utf-8",
    )
    remote = f"https://{_USER}:{_PAT}@github.com/{_REPO}.git"
    subprocess.run(["git", "-C", str(_REPO_ROOT), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "commit", "-m", f"add post: {slug}"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "push", remote, "main"], check=True
    )
    return f"{_SITE}/{slug}/"
