import openai
import re

from discord.ext import commands

import discord, random

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!" ,intents=discord.Intents.all())


OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'
DISCORD_BOT_KEY = 'YOIUR_DISCORD_BOT_KEY'
SERVER_IDS = ['YOUR_SERVER_IDS']

openai.api_key = OPENAI_API_KEY

history = dict()


def add_history(user: str, text: str, bot_answer: str):
    if not user in history:
        history[user] = []
    pair = dict(
        prompt=text,
        answer=bot_answer
    )
    history[user] = history[user][-9:] + [pair]


def get_history(user: str) -> list:
    if not user in history:
        return []
    return history[user]


def prompt_to_chat(user: str, prompt: str) -> str:
    previous = get_history(user)
    conversation = ""
    for chat in previous:
        conversation += f"Human: {chat['prompt']}\n" \
                        f"Bot: {chat['answer']}\n"
    return conversation + "\n" + f"Human: {prompt}"


def clean_bot_answer(answer: str) -> str:
    answer = answer.strip()
    answer = re.sub(r"^(Human|Bot|Robot|AI):\s*", "", answer)
    return answer


def chat_with_gpt(
    user: str,
    prompt: str,
    max_tokens: int = None,
    use_history: bool = None
) -> str:
    if max_tokens is None:
        max_tokens = 200
    if use_history is None or use_history == True:
        prompt = prompt_to_chat(user, prompt)
    print('prompt:', prompt)
    bot_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.25
    )
    print('bot response:', bot_response)
    bot_answer = '\n'.join([clean_bot_answer(choice.text) for choice in bot_response.choices])
    add_history(user, prompt, bot_answer)
    return bot_answer


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    # print(message)

    user = message.author
    if user == client.user:
        return

    text = message.content
    send = message.channel.send

    if text.startswith('!chat '):

    
        prompt = text[6:]
        try:
            # 여러 채널에서 다른 문맥을 갖고 싶다면
            # user 가 아니라 채널을 포함한 f"{user}{message.channel}" 로 변경
            bot_answer = chat_with_gpt(user, prompt)
            #await message.channel.send(f"> Your prompt is: {prompt}\nAnswer: {bot_answer}"
            await send(f"{bot_answer}")
        except:
            await send(f"Sorry, Failed to answer")

    if text.startswith('!help'):
        await send("!help : 모든 명령어 표시\n!chat : 채팅하기 \n!주사위/숫자 : 숫자의 최대치 만큼 주사위 ")
        
    if text.startswith('!주사위/'):
        strmsg = str(text)
        parts = strmsg.split('/')
        print(parts)
        limit = int(parts[1])
        random_num = random.randint(1, int(limit))
        await send(str(random_num) + "가 나왔습니다!")

client.run(DISCORD_BOT_KEY)