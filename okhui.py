import discord
import openai
import re
import keys

from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!" ,intents=discord.Intents.all())

OPENAI_API_KEY = keys.OPENAI_API_KEY
DISCORD_BOT_KEY = keys.DISCORD_BOT_KEY
SERVER_IDS = keys.SERVER_IDS

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
    answer = re.sub(r"^(\w.+\:) ", "", answer)
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


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print(f"{bot.user.name} connected.")


@bot.event
async def on_message(message):
    # print(message)

    user = message.author
    if user == bot.user:
        return

    text = message.content
    if text.startswith('!chat '):
        prompt = text[6:]
        try:
            # 여러 채널에서 다른 문맥을 갖고 싶다면
            # user 가 아니라 채널을 포함한 f"{user}{message.channel}" 로 변경
            bot_answer = chat_with_gpt(user, prompt)
            await message.channel.send(f"> Your prompt is: {prompt}\nAnswer: {bot_answer}")
        except:
            await message.channel.send(f"> Your prompt is: {prompt}\nSorry, Failed to answer")


@bot.add_command(guild_id=SERVER_IDS)
@commands(
    name="prompt",
    type=str,
    description="프롬프트를 적어주세요."
)
@commands(
    name="max_length",
    type=int,
    description="AI가 출력할 수 있는 최대 답변 길이. (기본값: 500)",
    required=False,
)
@commands(
    name="refresh",
    type=str,
    description="대화를 새로 시작합니다. (yes or no)",
    required=False,
)
async def chat(context, prompt: str, max_length: int, refresh: str):
    await context.defer()
    try:
        user = context.author
        # 여러 채널에서 다른 문맥을 갖고 싶다면
        # user 가 아니라 채널을 포함한 f"{user}{context.channel}" 로 변경
        use_history = (refresh or 'no').startswith('n')
        bot_answer = chat_with_gpt(user, prompt, max_tokens=max_length, use_history=use_history)
        await context.respond(f"> Prompt: {prompt}\n{bot_answer}")
    except Exception as err:
        await context.respond(f"> Prompt: {prompt}\n" \
                              f"Sorry, failed to answer\n" \
                              f"> {str(err)}")


def summarize_prompt(prompt: str):
    bot_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt + "\nSummarize sentence under 2000 lengths:",
        max_tokens=3000,
        temperature=0.0
    )
    return '\n'.join([choice.text for choice in bot_response.choices])
