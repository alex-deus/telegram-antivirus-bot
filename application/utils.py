import os
from pathlib import Path
from typing import Tuple

import motor.motor_asyncio
import aiohttp
import ujson
from aiofile import async_open
from aiogram import Bot, Dispatcher
from aiogram.types import ChatType, Message, ContentType
from aiohttp import FormData

from application.config import config

__all__ = ["get_bot"]

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongo_dsn)
mongo_db = mongo_client.main


def get_bot() -> Tuple[Bot, Dispatcher]:
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher(bot)

    dp.register_message_handler(process_messages, content_types=[ContentType.DOCUMENT])

    return bot, dp


async def process_messages(message: Message) -> None:
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    file_name = f"{message.chat.id}_{message.from_user.id}_{message.document.file_id}_{message.document.file_name}"
    file_path = Path.cwd() / "files" / file_name
    await message.document.download(file_path)

    await message.delete()

    text = (
        f"User @{message.from_user.username} has sent "
        f"file='{message.document.file_name}' with caption='{message.text or ''}'. "
        f"The message was removed. The file will be check by antivirus."
    )
    sent_message = await message.bot.send_message(message.chat.id, text)

    async with async_open(file_path, "rb") as afp:
        file_data = await afp.read()

    data = FormData()
    data.add_field(
        config.clam_key, file_data, filename=message.document.file_name, content_type=message.document.mime_type
    )
    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        response = await session.post(f"{config.clam_url}/api/v1/scan", data=data)
        response_data = await response.json()

    viruses = response_data["data"]["result"][0]["viruses"]
    has_viruses = len(viruses) > 0

    await mongo_db.messages.insert_one({
        "v": "1.0",
        "bot": {
            "id": None,
            "full_name": None,
        },
        "chat": {
            "id": message.chat.id,
            "full_name": message.chat.full_name,
            "is_private": message.chat.type == ChatType.PRIVATE,
        },
        "sender": {
            "id": message.from_user.id,
            "username": message.from_user.username,
            "is_bot": message.from_user.is_bot,
        },
        "document": {
            "file_id": message.document.file_id,
            "file_unique_id": message.document.file_unique_id,
            "file_name": message.document.file_name,
            "mime_type": message.document.mime_type,
            "file_size": message.document.file_size,
        },
        "request_message": {
            "id": message.message_id,
            "text": message.caption,
            "date": message.date,
        },
        "antivirus": {
            "type": "clam",
            "viruses": viruses,
            "is_infected": has_viruses,
        }
    })

    if has_viruses:
        text = f"Oh, no, we found an issue: {viruses}"
        await message.bot.send_message(message.chat.id, text, reply_to_message_id=sent_message.message_id)
    else:
        text = f"File is OK"
        await message.bot.send_document(
            message.chat.id, file_data, caption=text, reply_to_message_id=sent_message.message_id
        )

    os.unlink(file_path)
