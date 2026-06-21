import os
import json
import asyncio
import logging
from pathlib import Path

from aiohttp import web
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# ЛОГИ
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# =========================
# ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL", "").rstrip("/")
MINI_APP_URL = os.getenv("MINI_APP_URL", "").rstrip("/")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
PORT = int(os.getenv("PORT", "10000"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения TELEGRAM_BOT_TOKEN")

if not PUBLIC_URL:
    raise RuntimeError("Не задана переменная окружения PUBLIC_URL")

if not MINI_APP_URL:
    raise RuntimeError("Не задана переменная окружения MINI_APP_URL")

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

# =========================
# КЛАВИАТУРА БОТА
# =========================

def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(
                text="Открыть Mini App",
                web_app=WebAppInfo(url=MINI_APP_URL),
            )
        ],
        [
            KeyboardButton(text="Помощь")
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def start_text() -> str:
    return (
        "Здравствуйте!\n\n"
        "Это демо Telegram Mini App для салона красоты.\n\n"
        "Внутри можно посмотреть услуги, цены, акцию и отправить заявку.\n\n"
        "Нажмите кнопку «Открыть Mini App» внизу чата."
    )


# =========================
# ОБРАБОТЧИКИ TELEGRAM-БОТА
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        start_text(),
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "Как пользоваться демо:\n\n"
        "1. Нажмите кнопку «Открыть Mini App» внизу чата.\n"
        "2. Заполните имя, услугу и комментарий.\n"
        "3. Нажмите «Отправить заявку».\n\n"
        "Если нужно узнать chat_id администратора, отправьте команду /myid.",
        reply_markup=main_keyboard(),
    )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_chat:
        return

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"Ваш chat_id:\n\n{chat_id}\n\n"
        "Скопируйте это число и добавьте его в Render в переменную ADMIN_CHAT_ID."
    )


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Получает данные, которые Mini App отправляет через Telegram.WebApp.sendData().
    """
    if not update.message or not update.message.web_app_data:
        return

    raw_data = update.message.web_app_data.data

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        await update.message.reply_text(
            "Заявка получена, но данные не удалось разобрать:\n\n"
            f"{raw_data}"
        )
        return

    name = data.get("name", "Не указано")
    service = data.get("service", "Не указано")
    comment = data.get("comment", "Без комментария")

    client_message = (
        "✅ Заявка получена\n\n"
        f"Имя: {name}\n"
        f"Услуга: {service}\n"
        f"Комментарий: {comment}\n\n"
        "Администратор получил информацию и сможет связаться с вами."
    )

    await update.message.reply_text(client_message)

    admin_message = (
        "📩 Новая заявка из Mini App\n\n"
        f"Имя клиента: {name}\n"
        f"Услуга: {service}\n"
        f"Комментарий: {comment}\n\n"
        "Источник: Beauty Mini App Demo"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=admin_message,
            )
        except Exception:
            logger.exception("Не удалось отправить заявку администратору")
    else:
        logger.warning("ADMIN_CHAT_ID не задан. Заявка администратору не отправлена.")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    text = update.message.text

    if text == "Помощь":
        await help_command(update, context)
        return

    await update.message.reply_text(
        "Нажмите кнопку «Открыть Mini App» внизу чата.",
        reply_markup=main_keyboard(),
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Ошибка при обработке обновления:", exc_info=context.error)


# =========================
# WEB-СЕРВЕР ДЛЯ MINI APP
# =========================

async def index_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "index.html")


async def style_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "style.css")


async def app_js_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "app.js")


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def telegram_webhook_handler(request: web.Request) -> web.Response:
    """
    Принимает обновления Telegram по webhook.
    """
    application: Application = request.app["telegram_application"]

    try:
        data = await request.json()
    except Exception:
        logger.exception("Не удалось прочитать JSON от Telegram")
        return web.Response(text="Bad Request", status=400)

    update = Update.de_json(data, application.bot)

    await application.process_update(update)

    return web.Response(text="OK")


def create_web_app(application: Application) -> web.Application:
    app = web.Application()

    app["telegram_application"] = application

    app.router.add_get("/", index_handler)
    app.router.add_get("/style.css", style_handler)
    app.router.add_get("/app.js", app_js_handler)
    app.router.add_get("/health", health_handler)

    app.router.add_post("/webhook", telegram_webhook_handler)

    return app


# =========================
# ЗАПУСК
# =========================

async def main() -> None:
    telegram_application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .updater(None)
        .build()
    )

    telegram_application.add_handler(CommandHandler("start", start))
    telegram_application.add_handler(CommandHandler("help", help_command))
    telegram_application.add_handler(CommandHandler("myid", myid_command))

    telegram_application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler)
    )

    telegram_application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    telegram_application.add_error_handler(error_handler)

    await telegram_application.initialize()
    await telegram_application.start()

    webhook_url = f"{PUBLIC_URL}/webhook"

    await telegram_application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    logger.info("Telegram webhook установлен: %s", webhook_url)
    logger.info("Mini App URL: %s", MINI_APP_URL)

    if ADMIN_CHAT_ID:
        logger.info("ADMIN_CHAT_ID задан: %s", ADMIN_CHAT_ID)
    else:
        logger.warning("ADMIN_CHAT_ID не задан")

    aiohttp_app = create_web_app(telegram_application)

    runner = web.AppRunner(aiohttp_app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info("Web-сервер запущен на порту %s", PORT)

    try:
        await asyncio.Event().wait()
    finally:
        await telegram_application.stop()
        await telegram_application.shutdown()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())