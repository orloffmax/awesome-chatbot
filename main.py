import os
from telethon.sync import TelegramClient, events


API_TOKEN = os.environ['API_TOKEN']
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=API_TOKEN)


@bot.on(events.ChatAction)
async def chat_action(event):
    if event.user_joined:
        user_entity = event.user
        chat_entity = event.chat

        if user_entity.username is not None:
            greetings = '@' + user_entity.username
        else:
            greetings = user_entity.first_name

        await bot.send_message(
            entity=chat_entity,
            message=f'Привет, {greetings}, как твои дела?'
        )


def main():
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
