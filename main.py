import os
from datetime import timedelta

from telethon.sync import TelegramClient, events
from telethon.tl.types import (
    PeerChannel,
    PeerUser,
    ReplyKeyboardMarkup,
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButton,
    KeyboardButtonUrl,
    KeyboardButtonCallback
)
import asyncpraw

from captcha_challenge import Captcha


API_TOKEN = os.environ['API_TOKEN']
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=API_TOKEN)

wait_captcha = {}

bad_words = [
    "какашка",
    "говняшка",
    "дурачок"
]

bad_guys = {}

reddit = asyncpraw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="python:awesome-bot:v1 (by u/orl412)"
)


@bot.on(events.NewMessage(pattern='/reddit'))
async def reddit_memes(event):
    subreddit = await reddit.subreddit("memes")
    async for submission in subreddit.new(limit=10):
        if submission.url[-4:] in ['.jpg', '.png', '.gif']:
            if isinstance(event.peer_id, PeerUser):
                entity = event.peer_id
            else:
                entity = event.chat

            await bot.send_message(
                entity=entity,
                message=submission.title,
                file=submission.url
            )
            break


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if isinstance(event.peer_id, PeerUser):
        keyboard_buttons = ReplyKeyboardMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButton(text="Меню")
                    ]
                )
            ]
        )

        await bot.send_message(
            entity=event.peer_id,
            message="Чтобы вызвать меню, нажмите на кнопку 'Меню'",
            buttons=keyboard_buttons
        )


@bot.on(events.NewMessage(pattern='Меню'))
async def menu(event):
    if isinstance(event.peer_id, PeerUser):
        inline_buttons = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonUrl(
                            text="Смотреть код на Github",
                            url="https://github.com/orloffmax/awesome-chatbot"
                        ),
                        KeyboardButtonCallback(
                            text="Сказать спасибо за видео",
                            data=b'thanks'
                        )
                    ]
                )
            ]
        )

        await bot.send_message(
            entity=event.peer_id,
            message="Выбери пункт меню:",
            buttons=inline_buttons
        )


@bot.on(events.CallbackQuery(data=b'thanks'))
async def thanks(event):
    await event.respond("Ставь лайк и подписывайся на канал, если нравится :)")


@bot.on(events.ChatAction())
async def chat_action(event):
    if event.user_joined:
        user_entity = event.user
        chat_entity = event.chat

        if user_entity.username is not None:
            greetings = '@' + user_entity.username
        else:
            greetings = user_entity.first_name

        captcha = Captcha()

        await bot.send_message(
            entity=chat_entity,
            message=f'Привет, {greetings}! Пожалуйста, введи капчу, чтобы подтвердить, что ты не бот.',
            file=captcha.captcha_image
        )

        wait_captcha[(user_entity.id, chat_entity.id)] = captcha.captcha_text


@bot.on(events.NewMessage())
async def new_message(event):
    if isinstance(event.peer_id, PeerChannel):
        peer_user = event.from_id
        peer_channel = event.peer_id

        user_entity = await bot.get_entity(peer_user)

        captcha = wait_captcha.get((peer_user.user_id, peer_channel.channel_id))

        if captcha is not None:
            if event.text != captcha:
                await event.respond('Капча введена неверно.')
                await bot.delete_messages(peer_channel, event.message)
                await bot.kick_participant(peer_channel, peer_user)
            else:
                await event.respond(f'Добро пожаловать, {user_entity.first_name}!')
                await bot.delete_messages(peer_channel, [event.message.id, event.message.id - 1])
                del wait_captcha[(peer_user.user_id, peer_channel.channel_id)]
                return

        if any(bad_word in event.text.lower() for bad_word in bad_words):
            if not bad_guys.get((peer_user.user_id, peer_channel.channel_id)):
                bad_guys[(peer_user.user_id, peer_channel.channel_id)] = 1
            else:
                bad_guys[(peer_user.user_id, peer_channel.channel_id)] += 1

            await bot.delete_messages(
                entity=peer_channel,
                message_ids=[event.message]
            )

            message = ""
            match bad_guys[(peer_user.user_id, peer_channel.channel_id)]:
                case 1:
                    message = f"{user_entity.first_name}, не ругайся! Иначе ограничу доступ к сообщениям."
                case 2:
                    await bot.edit_permissions(
                        entity=peer_channel,
                        user=peer_user,
                        send_messages=False,
                        until_date=timedelta(minutes=1)
                    )
                    message = f"{user_entity.first_name} получил ограничение на отправку сообщений на 1 минуту."
                case 3:
                    await bot.kick_participant(
                        entity=peer_channel,
                        user=peer_user
                    )
                    message = f"{user_entity.first_name} был исключен за неоднократные нарушения правил чата."
                    del bad_guys[(peer_user.user_id, peer_channel.channel_id)]

            await bot.send_message(
                entity=peer_channel,
                message=message
            )


def main():
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
