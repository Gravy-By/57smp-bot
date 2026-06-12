import discord
import os
import asyncio
from discord import app_commands
from discord.ext import tasks  
from rcon.source import rcon
from mcstatus import JavaServer  

# --- НАСТРОЙКИ СЕРВЕРА 57 СМП ---
TOKEN = os.getenv('DISCORD_TOKEN')  
MINECRAFT_IP = '57.serveminecraft.net'
RCON_PORT = 25575  
RCON_PASSWORD = '57902'

# Твоя точная прямая ссылка на PNG-картинку
HELP_IMAGE_URL = "https://i.ibb.co/gLTrTMMv/pack.png"
# ----------------------------------------------------

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        self.update_status.start()

    @tasks.loop(seconds=30)
    async def update_status(self):
        try:
            server = await JavaServer.async_lookup(MINECRAFT_IP)
            status = await server.async_status()
            
            online = status.players.online
            max_players = status.players.max
            
            activity_text = f"на 57 СМП (Игроков: {online}/{max_players})"
            await self.change_presence(activity=discord.Game(name=activity_text))
            
        except Exception as e:
            print(f"Ошибка при получении онлайна: {e}")
            await self.change_presence(activity=discord.Game(name="на 57 СМП (Сервер оффлайн)"), status=discord.Status.dnd)

    @update_status.before_loop
    async def before_update_status(self):
        await self.wait_until_ready()

bot = MyBot()

def run_rcon_command(command):
    try:
        response = rcon(command, host=MINECRAFT_IP, port=RCON_PORT, password=RCON_PASSWORD)
        return response if response else "Команда выполнена"
    except Exception as e:
        return f"error: {e}"

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен!')

# 1. Реакция на упоминание бота
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        welcome_text = (
            "👋 **Привет! Рады видеть тебя на сервере 57 СМП!**\n"
            "Используй наши удобные слеш-команды:\n"
            "🔹 `/whitelist <ник>` — добавиться в вайтлист\n"
            "🔹 `/server` — узнать IP и версию сервера\n"
            "🔹 `/help` — информация о сервере\n"
            "🔹 `/rules` — правила сервера"
        )
        await message.reply(welcome_text)

# 2. Слеш-команда /start
@bot.tree.command(name="start", description="Показать приветственное меню")
async def start(interaction: discord.Interaction):
    await interaction.response.defer()
    welcome_text = (
        "👋 **Привет! Рады видеть тебя на сервере 57 СМП!**\n"
        "Выберите нужное действие:\n"
        "🔹 `/whitelist <ник>` — добавиться в вайтлист\n"
        "🔹 `/server` — узнать IP и версию сервера\n"
        "🔹 `/help` — информация о сервере\n"
        "🔹 `/rules` — правила сервера"
    )
    await interaction.followup.send(welcome_text)

# 3. Слеш-команда /whitelist
@bot.tree.command(name="whitelist", description="Добавить себя в белый список сервера")
@app_commands.describe(nickname="Ваш никнейм в Майнкрафт")
async def whitelist(interaction: discord.Interaction, nickname: str):
    clean_nickname = "".join(c for c in nickname if c.isalnum() or c == "_")
    
    if not clean_nickname:
        await interaction.response.send_message("❌ Некорректный никнейм!", ephemeral=True)
        return

    await interaction.response.defer()
    
    rcon_response = run_rcon_command(f"whitelist add {clean_nickname}")
    
    success_keywords = ["added", "добавлен", "already", "уже"]
    if any(word in rcon_response.lower() for word in success_keywords):
        await interaction.followup.send(f"✅ Игрок **{clean_nickname}** успешно добавлен в вайтлист сервера 57 СМП!")
    else:
        await interaction.followup.send(f"❌ Не удалось добавить игрока. Ответ сервера: `{rcon_response}`.")

# 4. Слеш-команда /help (С ТВОЕЙ ПРЯМОЙ КАРТИНКОЙ И БЕЗ ТЕКСТА ОПИСАНИЯ)
@bot.tree.command(name="help", description="Помощь и информация о сервере")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="🧭 57 СМП",
        description="Добро пожаловать!", # Текстовые поля очищены, как ты просил
        color=discord.Color.dark_red()
    )
    embed.set_image(url=HELP_IMAGE_URL) # Картинка берётся строго по твоей ссылке
    await interaction.followup.send(embed=embed)

# 5. Слеш-команда /rules
@bot.tree.command(name="rules", description="Правила сервера")
async def rules_command(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="📜 Правила сервера 57 СМП",
        color=discord.Color.orange()
    )
    embed.add_field(
        name="1. Честная игра", 
        value="Категорически запрещено играть с читами.", 
        inline=False
    )
    embed.add_field(
        name="2. Модификации интерфейса", 
        value="Запрещен фрикам (FreeCam) сквозь блоки, использование карт с включенным режимом пещер и радаром, отображающим игроков.", 
        inline=False
    )
    await interaction.followup.send(embed=embed)

# 6. Слеш-команда /server
@bot.tree.command(name="server", description="Информация для подключения к серверу")
async def server_command(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="🎮 Информация о сервере",
        color=discord.Color.green()
    )
    embed.add_field(name="🌐 IP адрес", value=f"`{MINECRAFT_IP}`", inline=True)
    embed.add_field(name="⚙️ Версия", value="`1.21.1`", inline=True)
    embed.add_field(
        name="📝 Что делать дальше?", 
        value="Пожалуйста, ознакомьтесь с правилами в команде `/rules` и не забудьте добавить себя в белый список с помощью `/whitelist <ваш_ник>`!", 
        inline=False
    )
    await interaction.followup.send(embed=embed)

bot.run(TOKEN)
