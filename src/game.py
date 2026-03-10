import random
from view import ButtonView, PiocheView
import discord


class Carte:
    def __init__(self, valeur):
        self.valeur = valeur
        self.visible = False
        self.deleted = False


class Game:
    def __init__(self, channel: discord.TextChannel, id_starter: int):
        self.channel = channel
        self.cartes = []
        self.lastturn = None
        self.defausse = None
        self.user_in_game = [id_starter]
        self.status = "wait"
        self.game = {}

    def init_pioche(self):
        for i in range(0, 5):
            self.cartes.append(-2)
        for i in range(0, 15):
            self.cartes.append(0)
        for i in range(0, 10):
            self.cartes.append(-1)
        for val in range(1, 13):
            for i in range(0, 10):
                self.cartes.append(val)
        random.shuffle(self.cartes)

    def join_game(self, id):
        self.user_in_game.append(id)

    def dealing_card(self):
        self.init_pioche()
        for user in self.user_in_game:
            self.game[user] = [
                        [Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop())],
                        [Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop())],
                        [Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop()), Carte(self.cartes.pop())],
                    ]
        self.defausse = self.cartes.pop()

    def get_max_player(self):
        id = None
        score_max = -42
        for user in self.game:
            score = 0
            for x in range(4):
                for y in range(3):
                    if self.game[user][y][x].visible:
                        score = score + self.game[user][y][x].valeur
            if score > score_max:
                id = user
                score_max = score
        return id

    async def start_game(self):
        for user in self.game:
            view = ButtonView(self.game[user], True, False, user)
            message = await self.channel.send(content=f"<@{user}> choisissez votre 1ere carte", view=view)
            while True:
                await view.wait()

                if view.value:
                    self.game[user][view.y][view.x].visible = True
                    break
                view = ButtonView(self.game[user], True, False, user)
                await message.edit(view=view)

            view = ButtonView(self.game[user], True, False, user)
            message = await self.channel.send(content=f"<@{user}> choisissez votre 2eme carte", view=view)
            while True:
                await view.wait()

                if view.value:
                    self.game[user][view.y][view.x].visible = True
                    break
                view = ButtonView(self.game[user], True, False, user)
                await message.edit(view=view)

        self.order = []
        self.order.append(self.get_max_player())
        for user in self.game:
            if user not in self.order:
                self.order.append(user)
        await self.boucle_game()

    async def draw_message(self, user):
        view = PiocheView(self.defausse, user)
        message = await self.channel.send(content=f"<@{user}> piochez ou choisissez la carte en defausse\n{self.show_game(user)}", view=view)
        while True:
            await view.wait()

            if view.value:
                if view.tag == "pioche":
                    return self.cartes.pop(0), False
                if view.tag == "defausse":
                    return self.defausse, True
            
            view = PiocheView(self.defausse, user)
            await message.edit(view=view)

    async def exenge_revele_card(self, user, defausse_actived: bool, carte_piocher: int):
        view = ButtonView(self.game[user], False, not defausse_actived, user)
        message = await self.channel.send(content=f"<@{user}> oû souhaitez vous mettre cette carte {carte_piocher} ?", view=view)
        while True:
            await view.wait()

            if view.value:
                if view.defausse:
                    self.defausse = carte_piocher
                    view_revele = ButtonView(self.game[user], True, False, user)
                    message_revele = await self.channel.send(content=f"<@{user}> choisissez la carte a retourner", view=view_revele)
                    while True:
                        await view_revele.wait()

                        if view_revele.value:
                            self.game[user][view_revele.y][view_revele.x].visible = True
                            break
                        view_revele = ButtonView(self.game[user], True, False, user)
                        await message_revele.edit(view=view_revele)
                    break
                else:
                    self.game[user][view.y][view.x].visible = True
                    self.defausse = self.game[user][view.y][view.x].valeur
                    self.game[user][view.y][view.x].valeur = carte_piocher
                    break
            view = ButtonView(self.game[user], False, not defausse_actived, user)
            await message.edit(view=view)

    async def player_turn(self, user):
        carte_piocher, defausse_actived = await self.draw_message(user)
        await self.exenge_revele_card(user, defausse_actived, carte_piocher)
        self.check_colone(user)
        await self.channel.send(content=f"<@{user}>\n{self.show_game(user)}", delete_after=60)
        if self.lastturn is None and self.check_if_last(user):
            self.lastturn = user
            await self.channel.send(content=f"# <@{user}> a revelé sa derniere carte le dernier tour commence !")

    async def boucle_game(self):
        while True:
            for user in self.order:
                if user == self.lastturn:
                    await self.end_game()
                    break
                await self.player_turn(user)
            if self.status == "ending":
                self.status = None
                break

    def check_colone(self, id):
        for x in range(4):
            if not self.game[id][0][x].deleted:
                if self.game[id][0][x].visible and self.game[id][1][x].visible and self.game[id][2][x].visible:
                    if self.game[id][0][x].valeur == self.game[id][1][x].valeur and self.game[id][1][x].valeur == self.game[id][2][x].valeur:
                        self.game[id][0][x].deleted = True
                        self.game[id][1][x].deleted = True
                        self.game[id][2][x].deleted = True
                        self.defausse = self.game[id][2][x].valeur

    def show_game(self, id):
        return "```" + "\n".join(
            " ".join(
                f"{(
                    'X' if not case.visible
                    else case.valeur if not case.deleted
                    else ''
                ):>{4}}"
                for case in line
            )
            for line in self.game[id]
        ) + "```"

    def check_if_last(self, id):
        for x in range(4):
            for y in range(3):
                if not self.game[id][y][x].visible:
                    return False
        return True

    async def end_game(self):
        score_final = {}
        for user in self.game:
            for x in range(4):
                for y in range(3):
                    self.game[user][y][x].visible = True
            self.check_colone(user)
        for user in self.game:
            score_f = 0
            for x in range(4):
                for y in range(3):
                    if not self.game[user][y][x].deleted:
                        score_f = score_f + self.game[user][y][x].valeur
            await self.channel.send(content=f"<@{user}> score : {score_f}\n{self.show_game(user)}")
            score_final[user] = score_f
        top = sorted(score_final.items(), key=lambda x: x[1])
        self.status = "ending"
        if top[0][0] != self.lastturn:
            score_final[self.lastturn] = score_final[self.lastturn] * 2
            await self.channel.send(content=f"# <@{self.lastturn}> a terminé en premier.e mais n'a pas le meilleur score: score doublé !")
        top = sorted(score_final.items(), key=lambda x: x[1])
        embed = discord.Embed(
            title=f"🏆 Resultat",
            color=discord.Color.dark_gold()
        )
        for i, (userid, score) in enumerate(top, start=1):
            user_discord = await self.channel.guild.fetch_member(userid)
            embed.add_field(
                name=f"{i}. {user_discord.name}",
                value=f"Score : **{score}**",
                inline=False
            )
        await self.channel.send(content="", embed=embed)
