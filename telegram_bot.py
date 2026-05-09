"""Telegram /generate 명령으로 전체 파이프라인을 실행한다."""
import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

from prompt_generator import generate_prompt
from image_generator import generate_image
from site_publisher import publish

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_ALLOWED_CHAT = os.getenv("TELEGRAM_CHAT_ID")
_TMP = Path("/tmp/hermes_image.png")

async def start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! /generate <한국어 키워드> 형식으로 입력하면 "
        "AI 이미지를 생성해 갤러리에 게시합니다."
    )

async def generate_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if _ALLOWED_CHAT and chat_id != _ALLOWED_CHAT:
        await update.message.reply_text("권한이 없습니다.")
        return
    keyword = " ".join(ctx.args).strip()
    if not keyword:
        await update.message.reply_text("사용법: /generate 한국어 키워드")
        return
    msg = await update.message.reply_text(f"🎨 '{keyword}' 처리 시작…\n1/4 영문 프롬프트 생성 중")
    try:
        prompt = generate_prompt(keyword)
        await msg.edit_text(f"🎨 '{keyword}'\n2/4 이미지 생성 중 (30~60초)…")
        generate_image(prompt, _TMP)
        await msg.edit_text(f"🎨 '{keyword}'\n3/4 사이트 업로드 및 배포 중…")
        url = publish(keyword, prompt, _TMP)
        await msg.edit_text(
            f"✅ 완료!\nURL: {url}\n(GitHub Actions 빌드 후 1~2분 내 노출)"
        )
    except Exception as e:
        logging.exception("pipeline failed")
        await msg.edit_text(f"❌ 오류: {e}")

def main():
    app = Application.builder().token(_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_cmd))
    logging.info("bot polling…")
    app.run_polling()

if __name__ == "__main__":
    main()
