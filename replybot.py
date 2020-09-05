import json
from typing import List, Optional, Union

from loguru import logger
from telegram import Message, TelegramObject, Update, ChatAction
from telegram.ext import CallbackContext
from config import BOT_RETRIES, BOT_TIMEOUT, CHAT_ID
from utils import send_action, getusername, userinfo2json, get_chat_id
from retry import TelegramTimedOutRetry
import json

@send_action(ChatAction.TYPING)
def start_callback(update: Update, context: CallbackContext):
    """Send a message when the command ``/start`` is issued."""
    message = update.message
    message.reply_text("Hi，This is a demo of livegram like bot")
    userinfo2json(update, context)

@send_action(ChatAction.TYPING)
def help_callback(update: Update, context: CallbackContext):
    """Send a message when the command ``/help`` is issued."""
    message = update.message
    message.reply_text('DEMO Author: William Lee')


def prepare_params(attachment: TelegramObject, at: str, reply_to_id: int) -> Optional[dict]:
    """prepare params for bots' ``send_*``."""
    if isinstance(attachment, list):
        if len(attachment) > 0:
            attachment = attachment[0]
        else:
            return None

    params = attachment.to_dict()

    logger.debug(json.dumps(params))

    file_id = params.pop("file_id", None)
    if file_id is not None:
        params[at] = file_id

    params["chat_id"] = reply_to_id

    return params


def reply_callback(update: Update, context: CallbackContext):
    message: Message = update.message
    if message.chat_id == CHAT_ID:
        string = str(message)#[0:-1]
        string = string.replace("\'", '\"')
        string = string.replace("True", '1')
        string = string.replace("False", '0')
        with open('replyid.json', 'w') as outfile:
            outfile.write(string)
        with open('replyid.json') as outfile:
            data = json.load(outfile)
        msg_dict = data['reply_to_message']
        if 'forward_from' in msg_dict:
            msg_username = data['reply_to_message']['forward_from']['first_name']
        else:
            msg_username = data['reply_to_message']['forward_sender_name']
        reply_to_id = get_chat_id(msg_username)
        if message.text is not None:
            TelegramTimedOutRetry(
                retry_count=BOT_RETRIES,
                function=context.bot.send_message,
                function_kwargs={
                    "chat_id": reply_to_id,
                    "text": message.text,
                    "from_chat_id": message.chat_id,
                    "message_id": message.message_id,
                    "timeout": BOT_TIMEOUT,
                },
            ).retry()
        if message.effective_attachment is not None:
            for at in message.ATTACHMENT_TYPES:
                attachment: Union[TelegramObject, List[TelegramObject]] = getattr(message, at)
                if attachment is not None:

                    params = prepare_params(attachment, at, reply_to_id)
                    if params is None:
                        continue

                    params["timeout"] = BOT_TIMEOUT
                    TelegramTimedOutRetry(
                        retry_count=BOT_RETRIES,
                        function=getattr(context.bot, f"send_{at}"),
                        function_kwargs=params,
                    ).retry()

                    break
    else:
        TelegramTimedOutRetry(
            retry_count=BOT_RETRIES,
            function=context.bot.forward_message,
            function_kwargs={
                "chat_id": CHAT_ID,
                "from_chat_id": message.chat_id,
                "message_id": message.message_id,
                "timeout": BOT_TIMEOUT,
            },
        ).retry()


def forward_callback(update: Update, context: CallbackContext):
    """Forward the user message to ``CHAT_ID``.

    """
    message: Message = update.message
    userinfo2json(update, context)
    logger.info(message)
    if message.chat_id == CHAT_ID:
        pass
    else:
        TelegramTimedOutRetry(
            retry_count=BOT_RETRIES,
            function=context.bot.forward_message,
            function_kwargs={
                "chat_id": CHAT_ID,
                "from_chat_id": message.chat_id,
                "message_id": message.message_id,
                "timeout": BOT_TIMEOUT,
            },
        ).retry()


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning('Update "{}" caused error "{}"', update, context.error)
