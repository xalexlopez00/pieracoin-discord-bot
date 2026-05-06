import os
import random
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from economy import Economy
from games import spin_roulette, play_blackjack

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
DATA_FILE = os.getenv("DATABASE_FILE", "economy.json")
DAILY_REWARD = int(os.getenv("DAILY_REWARD", "100"))
START_BALANCE = int(os.getenv("START_BALANCE", "500"))

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is required in .env or environment variables")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)
economy = Economy(DATA_FILE, start_balance=START_BALANCE, daily_reward=DAILY_REWARD)


def make_embed(title: str, description: str, color: discord.Color):
    return discord.Embed(title=title, description=description, color=color).set_footer(
        text=f"Usa {BOT_PREFIX}help para ver todos los comandos"
    )


def make_result_embed(title: str, description: str, color: discord.Color, fields: list[tuple[str, str, bool]]):
    embed = make_embed(title, description, color)
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    return embed


@bot.event
async def on_ready():
    print(f"Discord economy bot ready as {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = make_embed(
            "Argumento faltante",
            f"Falta un argumento para el comando `{ctx.command}`. Usa `{BOT_PREFIX}help` para ver la sintaxis correcta.",
            discord.Color.red(),
        )
        return await ctx.send(embed=embed)

    if isinstance(error, commands.BadArgument):
        embed = make_embed(
            "Argumento inválido",
            "Revisa los tipos de datos enviados. Asegúrate de usar números donde se esperan cantidades y menciones válidas.",
            discord.Color.red(),
        )
        return await ctx.send(embed=embed)

    if isinstance(error, commands.MemberNotFound):
        embed = make_embed(
            "Usuario no encontrado",
            "No pude encontrar ese miembro. Usa una mención válida o revisa el nombre.",
            discord.Color.red(),
        )
        return await ctx.send(embed=embed)

    if isinstance(error, commands.CommandNotFound):
        return

    embed = make_embed(
        "Error interno",
        "Ocurrió un error desconocido. Intenta de nuevo más tarde.",
        discord.Color.red(),
    )
    await ctx.send(embed=embed)


COMMAND_HELP = {
    "balance": {
        "usage": f"{BOT_PREFIX}balance [@usuario]",
        "description": "Muestra el saldo del wallet y del banco de un usuario. Si no se indica usuario, muestra el tuyo.",
        "example": f"{BOT_PREFIX}balance @Amigo",
    },
    "deposit": {
        "usage": f"{BOT_PREFIX}deposit <cantidad>",
        "description": "Deposita monedas del wallet al banco para guardarlas con seguridad.",
        "example": f"{BOT_PREFIX}deposit 100",
    },
    "withdraw": {
        "usage": f"{BOT_PREFIX}withdraw <cantidad>",
        "description": "Retira monedas del banco al wallet para apostar o enviar.",
        "example": f"{BOT_PREFIX}withdraw 50",
    },
    "pay": {
        "usage": f"{BOT_PREFIX}pay @usuario <cantidad>",
        "description": "Envía monedas desde tu wallet a otro miembro del servidor.",
        "example": f"{BOT_PREFIX}pay @Amigo 25",
    },
    "daily": {
        "usage": f"{BOT_PREFIX}daily",
        "description": "Reclama tu recompensa diaria de PieraCoin. Solo se puede usar cada 24 horas.",
        "example": f"{BOT_PREFIX}daily",
    },
    "roulette": {
        "usage": f"{BOT_PREFIX}roulette <cantidad> <rojo|negro|verde>",
        "description": "Apuesta en la ruleta. Rojo/negro pagan 2x, verde paga 14x.",
        "example": f"{BOT_PREFIX}roulette 50 rojo",
    },
    "blackjack": {
        "usage": f"{BOT_PREFIX}blackjack <cantidad>",
        "description": "Juega blackjack contra el dealer. Si obtienes 21 natural, ganas 1.5x.",
        "example": f"{BOT_PREFIX}blackjack 100",
    },
    "leaderboard": {
        "usage": f"{BOT_PREFIX}leaderboard",
        "description": "Muestra el top 10 de usuarios con más PieraCoin en wallet + banco.",
        "example": f"{BOT_PREFIX}leaderboard",
    },
}


@bot.command(name="help")
async def show_help(ctx, command: str = None):
    if command:
        key = command.lower()
        if key in {"bal", "b"}:
            key = "balance"
        if key == "send":
            key = "pay"
        if key == "bj":
            key = "blackjack"

        if key not in COMMAND_HELP:
            embed = make_embed(
                "Comando desconocido",
                f"No encontré ayuda para `{command}`. Usa `{BOT_PREFIX}help` para ver la lista completa.",
                discord.Color.orange(),
            )
            return await ctx.send(embed=embed)

        help_info = COMMAND_HELP[key]
        embed = make_result_embed(
            f"Ayuda: {key}",
            help_info["description"],
            discord.Color.blue(),
            [
                ("Uso", help_info["usage"], False),
                ("Ejemplo", help_info["example"], False),
            ],
        )
        return await ctx.send(embed=embed)

    embed = make_embed(
        "PieraCoin Economy Bot",
        "Comandos de economía, ruleta, blackjack y banca para tu servidor Discord.",
        discord.Color.blue(),
    )
    embed.add_field(name=f"{BOT_PREFIX}help <comando>", value="Muestra ayuda detallada para un comando.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}balance", value="Muestra tu saldo en wallet y banco.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}deposit <cantidad>", value="Deposita dinero en el banco.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}withdraw <cantidad>", value="Retira dinero del banco a tu wallet.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}pay @usuario <cantidad>", value="Envía monedas a otro usuario.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}daily", value="Reclama tu recompensa diaria.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}roulette <cantidad> <rojo|negro|verde>", value="Apuesta en la ruleta.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}blackjack <cantidad>", value="Juega blackjack contra el dealer.", inline=False)
    embed.add_field(name=f"{BOT_PREFIX}leaderboard", value="Muestra el ranking de riqueza.", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="balance", aliases=["bal", "b"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    account = await economy.get_account(member.id)
    embed = make_result_embed(
        f"Saldo de {member.display_name}",
        "Aquí está la información de tu cuenta:",
        discord.Color.green(),
        [
            ("Wallet", f"{account['wallet']} PieraCoin", True),
            ("Banco", f"{account['bank']} PieraCoin", True),
            ("Total", f"{account['wallet'] + account['bank']} PieraCoin", False),
        ],
    )
    await ctx.send(embed=embed)


@bot.command(name="deposit")
async def deposit(ctx, amount: int):
    if amount <= 0:
        embed = make_embed("Cantidad inválida", "La cantidad debe ser mayor que cero.", discord.Color.red())
        return await ctx.send(embed=embed)

    success, message = await economy.deposit(ctx.author.id, amount)
    color = discord.Color.green() if success else discord.Color.red()
    embed = make_embed("Depósito", message, color)
    await ctx.send(embed=embed)


@bot.command(name="withdraw")
async def withdraw(ctx, amount: int):
    if amount <= 0:
        embed = make_embed("Cantidad inválida", "La cantidad debe ser mayor que cero.", discord.Color.red())
        return await ctx.send(embed=embed)

    success, message = await economy.withdraw(ctx.author.id, amount)
    color = discord.Color.green() if success else discord.Color.red()
    embed = make_embed("Retiro", message, color)
    await ctx.send(embed=embed)


@bot.command(name="pay", aliases=["send"])
async def pay(ctx, receiver: discord.Member, amount: int):
    if receiver.id == ctx.author.id:
        embed = make_embed("Pago inválido", "No puedes pagarte a ti mismo.", discord.Color.red())
        return await ctx.send(embed=embed)
    if amount <= 0:
        embed = make_embed("Cantidad inválida", "La cantidad debe ser mayor que cero.", discord.Color.red())
        return await ctx.send(embed=embed)

    success, message = await economy.transfer(ctx.author.id, receiver.id, amount)
    color = discord.Color.green() if success else discord.Color.red()
    embed = make_embed("Pago", message, color)
    await ctx.send(embed=embed)


@bot.command(name="daily")
async def daily(ctx):
    success, message = await economy.claim_daily(ctx.author.id)
    color = discord.Color.green() if success else discord.Color.orange()
    embed = make_embed("Recompensa diaria", message, color)
    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx):
    top = await economy.get_leaderboard(10)
    if not top:
        embed = make_embed("Ranking vacío", "Todavía no hay cuentas con saldo en el sistema.", discord.Color.orange())
        return await ctx.send(embed=embed)

    lines = []
    for rank, entry in enumerate(top, start=1):
        user_id = int(entry[0])
        total = int(entry[1])
        member = ctx.guild.get_member(user_id)
        display = member.display_name if member else f"Usuario {user_id}"
        lines.append(f"**{rank}. {display}** — {total} PieraCoin")

    embed = make_embed(
        "Ranking de riqueza",
        "Los usuarios con más PieraCoin en tu servidor:",
        discord.Color.gold(),
    )
    embed.add_field(name="Top 10", value="\n".join(lines), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="roulette")
async def roulette(ctx, amount: int, choice: str):
    choice = choice.lower()
    if amount <= 0:
        embed = make_embed("Cantidad inválida", "La cantidad debe ser mayor que cero.", discord.Color.red())
        return await ctx.send(embed=embed)
    if choice not in {"rojo", "negro", "verde", "red", "black", "green"}:
        embed = make_embed("Opción inválida", "Elige: rojo, negro o verde.", discord.Color.red())
        return await ctx.send(embed=embed)

    normalized = {
        "rojo": "red",
        "negro": "black",
        "verde": "green",
        "red": "red",
        "black": "black",
        "green": "green",
    }[choice]

    account = await economy.get_account(ctx.author.id)
    if account["wallet"] < amount:
        embed = make_embed("Fondos insuficientes", "No tienes suficientes monedas en wallet para esta apuesta.", discord.Color.red())
        return await ctx.send(embed=embed)

    won, payout, result_name, slot = spin_roulette(amount, normalized)
    if won:
        await economy.change_wallet(ctx.author.id, payout - amount)
        current = await economy.get_account(ctx.author.id)
        embed = make_result_embed(
            "Ruleta - Ganaste",
            f"La ruleta cayó en **{slot}**. {result_name}! Ganaste **{payout - amount}** PieraCoin.",
            discord.Color.green(),
            [
                ("Apuesta", f"{amount} PieraCoin", True),
                ("Pago total", f"{payout} PieraCoin", True),
                ("Saldo wallet", f"{current['wallet']} PieraCoin", False),
            ],
        )
    else:
        await economy.change_wallet(ctx.author.id, -amount)
        current = await economy.get_account(ctx.author.id)
        embed = make_result_embed(
            "Ruleta - Perdiste",
            f"La ruleta cayó en **{slot}**. {result_name}. Perdiste **{amount}** PieraCoin.",
            discord.Color.red(),
            [
                ("Apuesta", f"{amount} PieraCoin", True),
                ("Saldo wallet", f"{current['wallet']} PieraCoin", True),
            ],
        )
    await ctx.send(embed=embed)


@bot.command(name="blackjack", aliases=["bj"])
async def blackjack(ctx, bet: int):
    if bet <= 0:
        embed = make_embed("Cantidad inválida", "La apuesta debe ser mayor que cero.", discord.Color.red())
        return await ctx.send(embed=embed)

    account = await economy.get_account(ctx.author.id)
    if account["wallet"] < bet:
        embed = make_embed("Fondos insuficientes", "No tienes suficientes monedas en wallet para apostar.", discord.Color.red())
        return await ctx.send(embed=embed)

    outcome = play_blackjack(bet)
    await economy.change_wallet(ctx.author.id, outcome["net_change"])
    final_account = await economy.get_account(ctx.author.id)

    embed = make_result_embed(
        "Blackjack",
        outcome["description"],
        discord.Color.purple(),
        [
            ("Tus cartas", outcome["player_hand"], True),
            ("Cartas del dealer", outcome["dealer_hand"], True),
            ("Resultado", outcome["result"], False),
            ("Cambio en wallet", f"{outcome['net_change']} PieraCoin", True),
            ("Wallet restante", f"{final_account['wallet']} PieraCoin", True),
        ],
    )
    await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
