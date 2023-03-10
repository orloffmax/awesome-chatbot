import os
from telethon.sync import TelegramClient, events
from captcha_challenge import Captcha


API_TOKEN = os.environ['API_TOKEN']
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=API_TOKEN)

wait_captcha = {}


@bot.on(events.ChatAction)
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


@bot.on(events.NewMessage)
async def new_message(event):
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


def main():
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
