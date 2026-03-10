import discord


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
        view.value = True
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
    def __init__(self, defausse, id_target):
        super().__init__()
        self.value = False
        self.add_item(PiocheButton("Pioche", "pioche", id_target))
        self.add_item(PiocheButton(f"Defausse ({defausse})", "defausse", id_target))
