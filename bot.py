import os
import random
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from economy import Economy
from games import spin_roulette, play_blackjack

# Cargar variables de entorno
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
DATABASE_URL = os.getenv("DATABASE_URL")
DAILY_REWARD = int(os.getenv("DAILY_REWARD", "100"))
START_BALANCE = int(os.getenv("START_BALANCE", "500"))

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is required in .env or environment variables")

# Configuración de Intents - Usamos .all() para evitar problemas de permisos
intents = discord.Intents.all() 

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)
economy = Economy(DATABASE_URL, start_balance=START_BALANCE, daily_reward=DAILY_REWARD)

# --- Utilidades ---

def make_embed(title: str, description: str, color: discord.Color):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"Usa {BOT_PREFIX}help para ver todos los comandos")
    return embed

def make_result_embed(title: str, description: str, color: discord.Color, fields: list):
    embed = make_embed(title, description, color)
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    return embed

# --- Eventos ---

@bot.event
async def on_ready():
    print(f"Discord economy bot ready as {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = make_embed("Argumento faltante", f"Usa `{BOT_PREFIX}help {ctx.command}` para ver cómo se usa.", discord.Color.red())
        return await ctx.send(embed=embed)
    if isinstance(error, commands.BadArgument):
        embed = make_embed("Argumento inválido", "Revisa los datos enviados (¿usaste números?).", discord.Color.red())
        return await ctx.send(embed=embed)
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Error no manejado: {error}")

# --- Comandos ---

COMMAND_HELP = {
    "balance": {"usage": f"{BOT_PREFIX}balance [@user]", "description": "Consulta tu saldo.", "example": f"{BOT_PREFIX}balance"},
    "deposit": {"usage": f"{BOT_PREFIX}deposit <cantidad>", "description": "Guarda dinero en el banco.", "example": f"{BOT_PREFIX}deposit 100"},
    "withdraw": {"usage": f"{BOT_PREFIX}withdraw <cantidad>", "description": "Saca dinero del banco.", "example": f"{BOT_PREFIX}withdraw 50"},
    "pay": {"usage": f"{BOT_PREFIX}pay @user <cantidad>", "description": "Envía dinero a alguien.", "example": f"{BOT_PREFIX}pay @Amigo 20"},
    "daily": {"usage": f"{BOT_PREFIX}daily", "description": "Reclama tu premio diario.", "example": f"{BOT_PREFIX}daily"},
    "roulette": {"usage": f"{BOT_PREFIX}roulette <cantidad> <color>", "description": "Apuesta en la ruleta.", "example": f"{BOT_PREFIX}roulette 10 rojo"},
    "blackjack": {"usage": f"{BOT_PREFIX}blackjack <cantidad>", "description": "Juega al 21.", "example": f"{BOT_PREFIX}blackjack 50"},
    "leaderboard": {"usage": f"{BOT_PREFIX}leaderboard", "description": "Mira quién es el más rico.", "example": f"{BOT_PREFIX}leaderboard"},
}

@bot.command(name="help")
async def show_help(ctx, command: str = None):
    if command:
        key = command.lower()
        if key in COMMAND_HELP:
            info = COMMAND_HELP[key]
            embed = make_result_embed(f"Ayuda: {key}", info["description"], discord.Color.blue(), [("Uso", info["usage"], False), ("Ejemplo", info["example"], False)])
            return await ctx.send(embed=embed)
    
    embed = make_embed("PieraCoin Economy", "Lista de comandos disponibles:", discord.Color.blue())
    for cmd, info in COMMAND_HELP.items():
        embed.add_field(name=f"{BOT_PREFIX}{cmd}", value=info["description"], inline=True)
    await ctx.send(embed=embed)

@bot.command(name="balance", aliases=["bal", "b"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    account = await economy.get_account(member.id)
    embed = make_result_embed(f"Saldo de {member.display_name}", "Estado de cuenta:", discord.Color.green(), [
        ("Wallet", f"{account['wallet']} 🪙", True),
        ("Banco", f"{account['bank']} 🏦", True),
        ("Total", f"{account['wallet'] + account['bank']} 💰", False)
    ])
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def daily(ctx):
    success, message = await economy.claim_daily(ctx.author.id)
    embed = make_embed("Recompensa Diaria", message, discord.Color.green() if success else discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="deposit")
async def deposit(ctx, amount: int):
    if amount <= 0: return await ctx.send("La cantidad debe ser positiva.")
    success, message = await economy.deposit(ctx.author.id, amount)
    await ctx.send(embed=make_embed("Banco", message, discord.Color.green() if success else discord.Color.red()))

@bot.command(name="withdraw")
async def withdraw(ctx, amount: int):
    if amount <= 0: return await ctx.send("La cantidad debe ser positiva.")
    success, message = await economy.withdraw(ctx.author.id, amount)
    await ctx.send(embed=make_embed("Banco", message, discord.Color.green() if success else discord.Color.red()))

@bot.command(name="pay")
async def pay(ctx, receiver: discord.Member, amount: int):
    if receiver.id == ctx.author.id: return await ctx.send("No puedes pagarte a ti mismo.")
    success, message = await economy.transfer(ctx.author.id, receiver.id, amount)
    await ctx.send(embed=make_embed("Transferencia", message, discord.Color.green() if success else discord.Color.red()))

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx):
    top = await economy.get_leaderboard(10)
    if not top: return await ctx.send("No hay datos aún.")
    
    lines = []
    for rank, entry in enumerate(top, start=1):
        user_id, total = int(entry[0]), int(entry[1])
        member = ctx.guild.get_member(user_id)
        name = member.display_name if member else f"ID: {user_id}"
        lines.append(f"**{rank}. {name}** — {total} PieraCoin")
    
    embed = make_embed("🏆 Ranking de Riqueza", "\n".join(lines), discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command(name="roulette")
async def roulette(ctx, amount: int, choice: str):
    choice = choice.lower()
    valid = {"rojo": "red", "negro": "black", "verde": "green", "red": "red", "black": "black", "green": "green"}
    if choice not in valid: return await ctx.send("Elige: rojo, negro o verde.")
    
    account = await economy.get_account(ctx.author.id)
    if account["wallet"] < amount: return await ctx.send("No tienes suficiente dinero en el wallet.")

    won, payout, res_name, slot = spin_roulette(amount, valid[choice])
    await economy.change_wallet(ctx.author.id, (payout - amount) if won else -amount)
    
    color = discord.Color.green() if won else discord.Color.red()
    msg = f"Cayó en **{slot}**. {'¡Ganaste!' if won else 'Perdiste.'} Recibes {payout} PieraCoin."
    await ctx.send(embed=make_embed("Ruleta", msg, color))

@bot.command(name="blackjack", aliases=["bj"])
async def blackjack(ctx, bet: int):
    account = await economy.get_account(ctx.author.id)
    if account["wallet"] < bet: return await ctx.send("No tienes suficiente dinero.")

    outcome = play_blackjack(bet)
    await economy.change_wallet(ctx.author.id, outcome["net_change"])
    
    embed = make_result_embed("Blackjack", outcome["description"], discord.Color.purple(), [
        ("Tus cartas", outcome["player_hand"], True),
        ("Dealer", outcome["dealer_hand"], True),
        ("Resultado", outcome["result"], False)
    ])
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
