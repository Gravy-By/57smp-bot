import discord
import os
from discord import app_commands
from rcon.source import rcon

# --- НАСТРОЙКИ СЕРВЕРА 57 СМП ---
TOKEN = os.getenv('DISCORD_TOKEN')  # Вставьте сюда токен из Discord Developer Portal
MINECRAFT_IP = '57.serveminecraft.net'
RCON_PORT = 25575  # Если хостинг использует другой порт для RCON, измените его здесь

# ИСПРАВЛЕНО: Для библиотеки rcon.source аргумент должен называться passwd, а не password
RCON_PASSWORD = '57902'

# Прямая ссылка на ваше фото
HELP_IMAGE_URL = "https://ibb.co"
# ----------------------------------------------------

class MyBot(discord.Client):
    def __init__(self):
        # Используем стандартные интенты для предотвращения дублирования событий
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

def run_rcon_command(command):
    try:
        # ИСПРАВЛЕНО: Изменено имя аргумента с password на passwd, чтобы библиотека работала корректно
        return rcon(command, host=MINECRAFT_IP, port=RCON_PORT, passwd=RCON_PASSWORD)
    except Exception as e:
        return f"error: {e}"

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен!')

# 1. Реакция на текстовые сообщения (ИСПРАВЛЕНО: теперь бот НЕ спамит дважды на любое слово)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Бот ответит только если пользователь напишет "привет", "старт" или упомянет бота
    content_lower = message.content.lower()
    if "привет" in content_lower or "старт" in content_lower or bot.user.mentioned_in(message):
        welcome_text = (
            "👋 **Привет! Рады видеть тебя на сервере 57 СМП!**\n"
            "Выберите нужное действие:\n"
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
    
    # Проверяем успешность ответа от сервера Minecraft
    if "Added" in rcon_response or "добавлен" in rcon_response.lower() or "already" in rcon_response:
        await interaction.followup.send(f"✅ Игрок **{clean_nickname}** успешно добавлен в вайтлист сервера 57 СМП!")
    else:
        await interaction.followup.send(f"❌ Не удалось добавить игрока. Ответ сервера: `{rcon_response}`")

# 4. Слеш-команда /help
@bot.tree.command(name="help", description="Помощь и информация о сервере")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="🧭 57 СМП",
        description=(
            "Сервер с парой особенностей:\n"
            "• Граница мира 600х600\n"
            "• Полная анонимность\n\n"
            "*Идея сервера:* `Пиротехник`\n"
            "*Технические админы:* `Слайм`, `Граву`"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_image(url=HELP_IMAGE_URL)
    await interaction.followup.send(embed=embed)

# 5. Слеш-команда /rules
@bot.tree.command(name="rules", description="Правила сервера")
async def rules_command(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(
        title="📜 Правила сервера 57 СМП",
        description=(
            "**1. Запрещено играть с любыми читами.**\n"
            "**2. Запрещен фрикам сквозь блоки**\n"
            "**3. Карты, с включенным режимом пещер и радаром**"
        ),
        color=discord.Color.orange()
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
    embed.add_field(name="⚙️ Версия", value="`1.21.11`", inline=True)
    embed.add_field(
        name="📝 Что делать дальше?", 
        value="Пожалуйста, ознакомьтесь с правилами в команде `/rules` и не забудьте добавить себя в белый список с помощью `/whitelist <ваш_ник>`!", 
        inline=False
    )
    await interaction.followup.send(embed=embed)

bot.run(TOKEN)
