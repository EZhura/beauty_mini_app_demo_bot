import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from aiohttp import web
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения TELEGRAM_BOT_TOKEN")

if not PUBLIC_URL:
    raise RuntimeError("Не задана переменная окружения PUBLIC_URL")

if not MINI_APP_URL:
    raise RuntimeError("Не задана переменная окружения MINI_APP_URL")

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

# =========================
# ДЕМО-ХРАНИЛИЩЕ ЗАЯВОК
# =========================
# Это временное хранилище в памяти.
# После перезапуска Render заявки в памяти очищаются.
# Google Sheets при этом сохраняет историю заявок.

REQUESTS = {}
REQUEST_COUNTER = 0


# =========================
# GOOGLE SHEETS
# =========================

def get_google_sheet():
    """
    Подключается к Google Sheets через service account.
    Возвращает первый лист таблицы.
    """
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        logger.warning(
            "GOOGLE_SHEET_ID или GOOGLE_SERVICE_ACCOUNT_JSON не заданы. "
            "Сохранение в Google Sheets отключено."
        )
        return None

    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes,
        )

        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

        return spreadsheet.sheet1

    except Exception:
        logger.exception("Не удалось подключиться к Google Sheets")
        return None


def save_request_to_google_sheets(request_data: dict) -> int | None:
    """
    Сохраняет новую заявку в Google Sheets.
    Возвращает номер строки, куда была записана заявка.
    """
    sheet = get_google_sheet()

    if not sheet:
        return None

    try:
        row = [
            request_data.get("request_id", ""),
            request_data.get("created_at", ""),
            request_data.get("name", ""),
            request_data.get("phone", ""),
            request_data.get("service", ""),
            request_data.get("master", ""),
            request_data.get("visit_date", ""),
            request_data.get("preferred_time", ""),
            request_data.get("comment", ""),
            request_data.get("telegram_name", ""),
            request_data.get("telegram_username", ""),
            request_data.get("telegram_id", ""),
            request_data.get("status", ""),
            request_data.get("source", ""),
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")

        all_values = sheet.get_all_values()
        row_number = len(all_values)

        logger.info("Заявка #%s сохранена в Google Sheets, строка %s", request_data.get("request_id"), row_number)

        return row_number

    except Exception:
        logger.exception("Не удалось сохранить заявку в Google Sheets")
        return None


def update_request_status_in_google_sheets(row_number: int | None, status: str) -> None:
    """
    Обновляет статус заявки в Google Sheets.
    Статус находится в колонке M, это 13-я колонка.
    """
    if not row_number:
        logger.warning("Номер строки Google Sheets не найден. Статус не обновлён.")
        return

    sheet = get_google_sheet()

    if not sheet:
        return

    try:
        status_column_number = 13
        sheet.update_cell(row_number, status_column_number, status)

        logger.info("Статус в Google Sheets обновлён: строка %s → %s", row_number, status)

    except Exception:
        logger.exception("Не удалось обновить статус заявки в Google Sheets")


# =========================
# КЛАВИАТУРЫ
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


def admin_request_keyboard(request_id: int, client_username: str | None = None) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить запись",
                callback_data=f"confirm_request:{request_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Нужно связаться",
                callback_data=f"need_contact:{request_id}",
            )
        ],
    ]

    if client_username:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Открыть Telegram клиента",
                    url=f"https://t.me/{client_username}",
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)


def start_text() -> str:
    return (
        "Здравствуйте!\n\n"
        "Это демо Telegram Mini App для салона красоты.\n\n"
        "Внутри можно посмотреть услуги, цены, акции, мастеров, FAQ "
        "и отправить заявку на запись.\n\n"
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
        "2. Выберите услугу или нажмите «Записаться» на карточке услуги.\n"
        "3. Заполните имя, телефон, мастера, дату и время.\n"
        "4. Нажмите «Отправить заявку».\n"
        "5. Администратор сможет подтвердить заявку одной кнопкой.\n"
        "6. Заявка дополнительно сохраняется в Google Sheets.\n\n"
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
    global REQUEST_COUNTER

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
    phone = data.get("phone", "Не указано")
    service = data.get("service", "Не указано")
    master = data.get("master", "Любой мастер")
    visit_date = data.get("visit_date", "Не указано")
    preferred_time = data.get("preferred_time", "Не указано")
    comment = data.get("comment", "Без комментария")

    user = update.effective_user

    if user:
        client_chat_id = user.id
        telegram_id = user.id
        telegram_username = f"@{user.username}" if user.username else "username не указан"
        username_for_button = user.username if user.username else None
        telegram_name = user.full_name or "Имя в Telegram не указано"
    else:
        client_chat_id = None
        telegram_id = "не указан"
        telegram_username = "не указан"
        username_for_button = None
        telegram_name = "не указано"

    REQUEST_COUNTER += 1
    request_id = REQUEST_COUNTER

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    request_data = {
        "request_id": request_id,
        "created_at": created_at,
        "client_chat_id": client_chat_id,
        "name": name,
        "phone": phone,
        "service": service,
        "master": master,
        "visit_date": visit_date,
        "preferred_time": preferred_time,
        "comment": comment,
        "telegram_name": telegram_name,
        "telegram_username": telegram_username,
        "telegram_id": telegram_id,
        "status": "Новая заявка",
        "source": "LAVANDA Beauty Studio Demo",
        "google_sheet_row": None,
    }

    google_sheet_row = await asyncio.to_thread(save_request_to_google_sheets, request_data)
    request_data["google_sheet_row"] = google_sheet_row

    REQUESTS[request_id] = request_data

    client_message = (
        "✅ Заявка получена\n\n"
        f"Номер заявки: #{request_id}\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Услуга: {service}\n"
        f"Мастер: {master}\n"
        f"Дата визита: {visit_date}\n"
        f"Выбранное время: {preferred_time}\n"
        f"Комментарий: {comment}\n\n"
        "Администратор получил информацию и сможет связаться с вами для подтверждения записи."
    )

    await update.message.reply_text(client_message)

    google_sheets_status = (
        f"Да, строка {google_sheet_row}"
        if google_sheet_row
        else "Нет / не настроено"
    )

    admin_message = (
        "📩 Новая заявка из Mini App\n\n"
        f"Номер заявки: #{request_id}\n"
        f"Дата создания: {created_at}\n"
        f"Имя клиента: {name}\n"
        f"Телефон: {phone}\n"
        f"Услуга: {service}\n"
        f"Мастер: {master}\n"
        f"Дата визита: {visit_date}\n"
        f"Выбранное время: {preferred_time}\n"
        f"Комментарий: {comment}\n\n"
        "Telegram-данные клиента:\n"
        f"Имя в Telegram: {telegram_name}\n"
        f"Username: {telegram_username}\n"
        f"Telegram ID: {telegram_id}\n\n"
        "Статус: Новая заявка\n"
        f"Google Sheets: {google_sheets_status}\n"
        "Источник: LAVANDA Beauty Studio Demo"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=admin_message,
                reply_markup=admin_request_keyboard(
                    request_id=request_id,
                    client_username=username_for_button,
                ),
            )
        except Exception:
            logger.exception("Не удалось отправить заявку администратору")
    else:
        logger.warning("ADMIN_CHAT_ID не задан. Заявка администратору не отправлена.")


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if not query:
        return

    if ADMIN_CHAT_ID and str(query.from_user.id) != str(ADMIN_CHAT_ID):
        await query.answer(
            "Эта кнопка доступна только администратору.",
            show_alert=True,
        )
        return

    await query.answer()

    data = query.data or ""

    if ":" not in data:
        return

    action, request_id_text = data.split(":", 1)

    try:
        request_id = int(request_id_text)
    except ValueError:
        await query.answer(
            "Не удалось определить номер заявки.",
            show_alert=True,
        )
        return

    request_data = REQUESTS.get(request_id)

    if not request_data:
        await query.answer(
            "Заявка не найдена. Возможно, сервис был перезапущен.",
            show_alert=True,
        )
        return

    client_chat_id = request_data.get("client_chat_id")

    if not client_chat_id:
        await query.answer(
            "Не удалось определить Telegram клиента.",
            show_alert=True,
        )
        return

    service = request_data.get("service", "Не указано")
    master = request_data.get("master", "Любой мастер")
    visit_date = request_data.get("visit_date", "Не указано")
    preferred_time = request_data.get("preferred_time", "Не указано")
    google_sheet_row = request_data.get("google_sheet_row")

    current_text = query.message.text if query.message else ""

    if action == "confirm_request":
        try:
            new_status = "Подтверждена"

            request_data["status"] = new_status

            await asyncio.to_thread(
                update_request_status_in_google_sheets,
                google_sheet_row,
                new_status,
            )

            await context.bot.send_message(
                chat_id=client_chat_id,
                text=(
                    "✅ Ваша запись подтверждена\n\n"
                    f"Номер заявки: #{request_id}\n"
                    f"Услуга: {service}\n"
                    f"Мастер: {master}\n"
                    f"Дата: {visit_date}\n"
                    f"Время: {preferred_time}\n\n"
                    "Ждём вас в салоне!\n"
                    "Если потребуется уточнение, администратор свяжется с вами."
                ),
            )

            await query.edit_message_text(
                text=(
                    f"{current_text}\n\n"
                    "✅ Статус: запись подтверждена администратором\n"
                    "Google Sheets: статус обновлён"
                )
            )

        except Exception:
            logger.exception("Не удалось подтвердить заявку")
            await query.answer(
                "Не удалось отправить подтверждение клиенту.",
                show_alert=True,
            )

    elif action == "need_contact":
        try:
            new_status = "Нужно связаться"

            request_data["status"] = new_status

            await asyncio.to_thread(
                update_request_status_in_google_sheets,
                google_sheet_row,
                new_status,
            )

            await context.bot.send_message(
                chat_id=client_chat_id,
                text=(
                    "💬 Администратору нужно уточнить детали записи\n\n"
                    f"Номер заявки: #{request_id}\n"
                    f"Услуга: {service}\n"
                    f"Дата: {visit_date}\n"
                    f"Время: {preferred_time}\n\n"
                    "Пожалуйста, ожидайте сообщение или звонок."
                ),
            )

            await query.edit_message_text(
                text=(
                    f"{current_text}\n\n"
                    "💬 Статус: требуется уточнение с клиентом\n"
                    "Google Sheets: статус обновлён"
                )
            )

        except Exception:
            logger.exception("Не удалось отправить клиенту сообщение об уточнении")
            await query.answer(
                "Не удалось отправить сообщение клиенту.",
                show_alert=True,
            )


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
    telegram_application.add_handler(CallbackQueryHandler(admin_callback_handler))

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

    if GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON:
        logger.info("Google Sheets переменные заданы")
    else:
        logger.warning("Google Sheets переменные не заданы или заданы не полностью")

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