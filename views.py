from typing import Coroutine
import discord


class RoleView(discord.ui.View):
    """For our support server."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Remove Role",
        style=discord.ButtonStyle.danger,
        custom_id="role_view:remove",
    )
    async def remove_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        role = interaction.guild.get_role(1134971094709850185)
        print(role)
        await interaction.user.remove_roles(role)
        await interaction.response.send_message(
            "Role Removed!", ephemeral=True, delete_after=3
        )


class VerifyView(discord.ui.View):
    callable: Coroutine

    def __init__(self, callable):
        super().__init__(timeout=None)
        self.callable = callable

    @discord.ui.button(
        label="認証を始める",
        style=discord.ButtonStyle.primary,
        custom_id="verify_view:start",
    )
    async def start_verify(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.callable(interaction)
