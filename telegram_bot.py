"""Telegram 봇: /generate, 생성, 계속 명령어로 차량 콘텐츠 자동화."""
import os
import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from prompt_generator import generate_prompt
from image_generator import generate_image
from site_publisher import publish
from car_content_generator import generate_car_items, reset_used

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_ALLOWED_CHAT = os.getenv("TELEGRAM_CHAT_ID")
_TMP = Path("/tmp/hermes_image.png")


def _is_allowed(chat_id: str) -> bool:
    return not _ALLOWED_CHAT or chat_id == _ALLOWED_CHAT


async def start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! 사용 가능한 명령:\n"
        "• /generate <한국어 키워드> — 단일 이미지 포스트 생성\n"
        "• 생성 — 차량 캐릭터 9개 자동 생성\n"
        "• 계속 — 새로운 9개 추가 생성 (중복 없음)\n"
        "• 초기화 — 사용된 캐릭터 목록 초기화"
    )


async def generate_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not _is_allowed(chat_id):
        await update.message.reply_text("권한이 없습니다.")
        return
    keyword = " ".join(ctx.args).strip()
    if not keyword:
        await update.message.reply_text("사용법: /generate 한국어 키워드")
        return
    msg = await update.message.reply_text(f"🌀 '{keyword}' 처리 시작…\n1/4 영문 프롬프트 생성 중")
    try:
        prompt = generate_prompt(keyword)
        await msg.edit_text(f"🌀 '{keyword}'\n2/4 이미지 생성 중 (30~60초)…")
        generate_image(prompt, _TMP)
        await msg.edit_text(f"🌀 '{keyword}'\n3/4 사이트 업로드 및 배포 중…")
        url = publish(keyword, prompt, _TMP)
        await msg.edit_text(f"✅ 완료!\nURL: {url}\n(GitHub Actions 빌드 후 1~2분 내 노출)")
    except Exception as e:
        logging.exception("pipeline failed")
        await msg.edit_text(f"❌ 오류: {e}")


async def _process_car_items(update: Update, items: list):
    """9개 아이템을 순차 처리"""
    total = len(items)
    for idx, item in enumerate(items, 1):
        char = item.get("character", "?")
        dialogue = item.get("dialogue", "")
        tip = item.get("tip", "")
        img_prompt = item.get("image_prompt", "")
        char_en = item.get("character_en", char)

        progress = await update.message.reply_text(
            f"🚗 {idx}/{total}: {char}\n💬 {dialogue}\n💡 {tip}\n\n⏳ 이미지 생성 중…"
        )
        try:
            generate_image(img_prompt, _TMP)
            await progress.edit_text(
                f"🚗 {idx}/{total}: {char}\n💬 {dialogue}\n💡 {tip}\n\n📤 사이트 업로드 중…"
            )
            url = publish(char, char_en, _TMP, character=char, dialogue=dialogue, tip=tip)
            with open(_TMP, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=(
                        f"🚗 {idx}/{total}: {char}\n"
                        f"💬 {dialogue}\n"
                        f"💡 {tip}\n"
                        f"🔗 {url}"
                    ),
                )
            await progress.delete()
        except Exception as e:
            logging.exception(f"item {idx} failed")
            await progress.edit_text(f"❌ {idx}/{total} {char} 실패: {e}")
        await asyncio.sleep(2)
    await update.message.reply_text(f"🎉 {total}개 모두 완료! '계속' 입력 시 새 9개 생성")


async def text_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not _is_allowed(chat_id):
        await update.message.reply_text("권한이 없습니다.")
        return

    text = (update.message.text or "").strip().lstrip("/")

    if text == "생성":
        await update.message.reply_text("🚗 차량 캐릭터 9개 추출 중… (30초~1분)")
        try:
            items = generate_car_items(9)
        except Exception as e:
            logging.exception("car items failed")
            await update.message.reply_text(f"❌ 아이템 생성 실패: {e}")
            return
        await _process_car_items(update, items)

    elif text == "계속":
        await update.message.reply_text("🚗 새로운 9개 추출 중… (중복 제외)")
        try:
            items = generate_car_items(9)
        except Exception as e:
            logging.exception("car items failed")
            await update.message.reply_text(f"❌ 아이템 생성 실패: {e}")
            return
        await _process_car_items(update, items)

    elif text == "초기화":
        reset_used()
        await update.message.reply_text("✅ 사용된 캐릭터 목록을 초기화했습니다.")


def main():
    app = Application.builder().token(_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    logging.info("bot polling…")
    app.run_polling()


if __name__ == "__main__":
    main()
