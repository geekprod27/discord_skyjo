import os
from game import Game
import discord
from discord import app_commands


intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

games = {}


@tree.command(
    name="init_game",
    description="init une game",
)
async def init_game(interaction: discord.Interaction, nb_ia: int = 0):
    global games
    await interaction.response.send_message("chargement ...")
    if interaction.channel.id in games:
        await interaction.edit_original_response(content="Une game est deja init dans ce channel")
        return
    games[interaction.channel.id] = Game(interaction.channel, interaction.user.id)
    for ia in range(nb_ia):
        games[interaction.channel.id].join_game("ia-" + str(ia))
    await interaction.edit_original_response(content="Game init")


@tree.command(
    name="join_game",
    description="join une game",
)
async def join_game(interaction: discord.Interaction):
    global games
    if interaction.channel.id not in games:
        await interaction.response.send_message("Aucune game dans ce channel")
        return
    if games[interaction.channel.id].status != "wait":
        await interaction.response.send_message("La game est deja en cours")
        return
    if interaction.user.id in games[interaction.channel.id].user_in_game:
        await interaction.response.send_message("Deja dans le game")
        return
    games[interaction.channel.id].join_game(interaction.user.id)
    await interaction.response.send_message("Inscription enregistée !")


@tree.command(
    name="start_game",
    description="Demarer une game",
)
async def start_game(interaction: discord.Interaction):
    global games
    if interaction.channel.id not in games:
        await interaction.response.send_message("Aucune game dans ce channel")
        return
    if games[interaction.channel.id].status != "wait":
        await interaction.response.send_message("La game est deja en cours")
        return
    await interaction.response.send_message("Demarrage de la partie")
    games[interaction.channel.id].dealing_card()
    await games[interaction.channel.id].start_game()
    games.pop(interaction.channel.id)
    await interaction.edit_original_response(content="Fin de la partie")


@bot.event
async def on_ready():
    global message
    await tree.sync()
    print('Bot is ready !')

if __name__ == '__main__':
    bot.run(os.getenv("TOKEN"))
