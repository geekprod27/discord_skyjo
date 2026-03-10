import os
import random
import discord
from discord import app_commands


intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


class Carte:
    def __init__(self, valeur):
        self.valeur = valeur
        self.visible = False
        self.deleted = False


cartes = []
lastturn = None
defausse = None
user_in_game = []
game_status = None
game = {}

class SkyButton(discord.ui.Button):
    def __init__(self, x: int, y: int, data, disable_if_visible: bool, id_target):
        label = "X"
        if data[y][x].visible:
            label = str(data[y][x].valeur)
        super().__init__(style=discord.ButtonStyle.secondary, label=label, row=y)
        if data[y][x].visible:
            self.disabled = disable_if_visible
        else:
            self.style = discord.ButtonStyle.green
        self.x = x
        self.y = y
        self.user = id_target

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            return
        await interaction.response.edit_message(content="Action confirmée", view=None, delete_after=3)
        view = self.view
        view.x = self.x
        view.y = self.y
        view.value = True
        view.stop()

class DefButton(discord.ui.Button):
    def __init__(self, id_target, label, row, style):
         super().__init__(label=label, row=row, style=style)
         self.user = id_target
    async def callback(self, interaction):
        if interaction.user.id != self.user:
            return
        await interaction.response.edit_message(content="Action confirmée", view=None, delete_after=3)
        view = self.view
        view.value = True
        view.defausse = True
        view.stop() 
        

class PiocheButton(discord.ui.Button):
    def __init__(self, label: str, tag: str, id_target):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.tag = tag
        self.user = id_target

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            return
        await interaction.response.edit_message(content="Action confirmée", view=None, delete_after=3)
        view = self.view
        view.tag = self.tag
        view.stop()

class ButtonView(discord.ui.View):
    def __init__(self, data, disable_if_visible, but_defausse: bool, id_target):
        super().__init__()
        self.value = False
        self.defausse = False
        for x in range(4):
            for y in range(3):
                if not data[y][x].deleted:
                    self.add_item(SkyButton(x, y, data, disable_if_visible, id_target))
        if but_defausse:
            self.add_item(DefButton(id_target=id_target, label="Défausser", row=4, style=discord.ButtonStyle.danger))

class PiocheView(discord.ui.View):
    def __init__(self, id_target):
        super().__init__()
        self.label = None
        self.add_item(PiocheButton("Pioche", "pioche", id_target))
        self.add_item(PiocheButton(f"Defausse ({defausse})", "defausse", id_target))

def check_if_last(id):
    for x in range(4):
        for y in range(3):
            if not game[id][y][x].visible:
                return False
    return True

def init_cartes():
    for i in range(0, 5):
        cartes.append(-2)
    for i in range(0, 15):
        cartes.append(0)
    for i in range(0, 10):
        cartes.append(-1)
    for val in range(1, 13):
        for i in range(0, 10):
            cartes.append(val)
    random.shuffle(cartes)

def get_max_player():
    id = None
    score_max = -42
    for user in game:
        score = 0
        for x in range(4):
            for y in range(3):
                if game[user][y][x].visible:
                    score = score + game[user][y][x].valeur
        if score > score_max:
            id = user
            score_max = score
    return id

def show_game(id):
    return "```" + "\n".join(
    " ".join(
        f"{(
            'X' if not case.visible
            else case.valeur if not case.deleted
            else ''
        ):>{4}}"
        for case in ligne
    )
    for ligne in game[id]
) + "```"

def check_colone(id):
    global defausse
    for x in range(4):
        if not game[id][0][x].deleted:
            if game[id][0][x].visible and game[id][1][x].visible and game[id][2][x].visible:
                if game[id][0][x].valeur == game[id][1][x].valeur and game[id][1][x].valeur == game[id][2][x].valeur:
                    game[id][0][x].deleted = True
                    game[id][1][x].deleted = True
                    game[id][2][x].deleted = True
                    defausse = game[id][2][x].valeur
            

async def end_game(channel: discord.TextChannel):
    global game_status, game
    score_final = {}
    for user in game:
        for x in range(4):
            for y in range(3):
                game[user][y][x].visible = True
        check_colone(user)
    for user in game:
        score_f = 0
        for x in range(4):
            for y in range(3):
                if not game[user][y][x].deleted:
                    score_f = score_f + game[user][y][x].valeur
        await channel.send(content=f"<@{user}> score : {score_f}\n{show_game(user)}")
        score_final[user] = score_f
    top = sorted(score_final.items(), key=lambda x: x[1])
    game_status = "ending"
    if top[0][0] != lastturn:
        score_final[lastturn] = score_final[lastturn] * 2
        await channel.send(content=f"# <@{lastturn}> a terminé en premier.e mais n'a pas le meilleur score: score doublé !")
    top = sorted(score_final.items(), key=lambda x: x[1])
    embed = discord.Embed(
        title=f"🏆 Resultat",
        color=discord.Color.dark_gold()
    )
    guild = channel.guild
    for i, (userid, score) in enumerate(top, start=1):
        user_discord = await guild.fetch_member(userid)
        embed.add_field(
            name=f"{i}. {user_discord.name}",
            value=f"Score : **{score}**",
            inline=False
        )
    await channel.send(content="", embed=embed)



async def boucle_game(order: list, channel: discord.TextChannel):
    global defausse, game_status, lastturn
    while True:
        for user in order:
            carte_piocher = None
            defausse_actived = False
            if user == lastturn:
                await end_game(channel)
                break
            while True:
                view = PiocheView(user)
                message = await channel.send(content=f"<@{user}> piochez ou choisissez la carte en defausse\n{show_game(user)}", view=view)
                await view.wait()
            
                if view.tag == "pioche":
                    carte_piocher = cartes.pop(0)
                    break
                if view.tag == "defausse":
                    defausse_actived = True
                    carte_piocher = defausse
                    break
                await message.delete()
            
            while True:
                view = ButtonView(game[user], False, not defausse_actived, user)
                message = await channel.send(content=f"<@{user}> oû souhaitez vous mettre cette carte {carte_piocher} ?", view=view)
                await view.wait()
            
                if view.value == True:
                    if view.defausse:
                        defausse = carte_piocher
                        while True:
                            view = ButtonView(game[user], True, False, user)
                            message = await channel.send(content=f"<@{user}> choisissez la carte a retourner", view=view)
                            await view.wait()
                            
                            if view.value == True:
                                game[user][view.y][view.x].visible = True
                                break
                            message.delete()
                        break
                    else:
                        game[user][view.y][view.x].visible = True
                        defausse = game[user][view.y][view.x].valeur
                        game[user][view.y][view.x].valeur = carte_piocher
                        break
                await message.delete()
            check_colone(user)
            await channel.send(content=f"<@{user}>\n{show_game(user)}", delete_after=60)
            if lastturn is None and check_if_last(user):
                lastturn = user
                await channel.send(content=f"# <@{user}> a revelé sa derniere carte le dernier tour commence !")
        if game_status == "ending":
            game_status = None
            break
            

async def first_tour(channel: discord.TextChannel):
    global game, defausse
    for user in game:
        while True:
            view = ButtonView(game[user], True, False, user)
            message = await channel.send(content=f"<@{user}> choisissez votre 1ere carte", view=view)
            await view.wait()
            
            if view.value == True:
                game[user][view.y][view.x].visible = True
                break
            message.delete()

        while True:
            view = ButtonView(game[user], True, False, user)
            message = await channel.send(content=f"<@{user}> choisissez votre 2eme carte", view=view)
            await view.wait()

            if view.value == True:
                game[user][view.y][view.x].visible = True
                break
            message.delete()
    
    ordre = []
    ordre.append(get_max_player())
    for user in game:
        if user not in ordre:
            ordre.append(user)
    await boucle_game(ordre, channel)

    

@tree.command(
    name="init_game",
    description="init une game",
)
async def init_game(interaction):
    global user_in_game, game_status, lastturn
    if game_status is not None:
        await interaction.response.send_message("Game deja en init")
        return
    user_in_game = []
    lastturn = None
    user_in_game.append(interaction.user.id)
    game_status = "wait"
    init_cartes()
    await interaction.response.send_message("Game init")

@tree.command(
    name="join_game",
    description="join une game",
)
async def join_game(interaction):
    global user_in_game, game_status
    if game_status != "wait":
        await interaction.response.send_message("Game non init ou en cours")
        return
    if interaction.user.id in user_in_game:
        await interaction.response.send_message("Deja dans le game")
        return
    await interaction.response.send_message("Inscription enregistée !")
    user_in_game.append(interaction.user.id)


@tree.command(
    name="start_game",
    description="join une game",
)
async def start_game(interaction):
    global user_in_game, game_status, game, defausse
    if game_status != "wait":
        await interaction.response.send_message("Game non init ou en cours")
        return
    game_status = "in_progress"
    await interaction.response.send_message("Game started")
    for user in user_in_game:
        game[user] = [[Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop())],
                      [Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop())],
                      [Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop()), Carte(cartes.pop())],]
    defausse = cartes.pop()
    await first_tour(interaction.channel)


@bot.event
async def on_ready():
    global message
    await tree.sync()
    print('Bot is ready !')

if __name__ == '__main__':
    bot.run(os.getenv("TOKEN"))
