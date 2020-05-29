import json
import logging

import discord
from discord.ext import commands
from datetime import datetime
from jishaku.paginators import PaginatorEmbedInterface

_DEFAULTS = {}
_PERMS = {
    "read_messages": True,
    "send_messages": True,
    "embed_links": True,
    "attach_files": True,
    "manage_messages": True,
    "add_reactions": True,
    "use_external_emojis": True
}


class GuildManager(commands.Cog):
    """
    A modular cog to help with guild management on discord.py bots.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loaded = datetime.utcnow()
        try:
            with open("./gman.data") as rfile:
                data = json.load(rfile)
            self.data = data
            logging.info(f"[GUILDMANAGER] loaded data from ./gman.data")
        except Exception as e:
            logging.warning(f"[GUILDMANAGER] Failed to load data from ./gman.data ({str(e)}), creating a new file"
                            f" with default settings.")
            with open("./gman.data", "w+") as wfile:
                json.dump(_DEFAULTS, wfile)
                self.data = _DEFAULTS

    async def cog_check(self, ctx: commands.Context):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()

        return True

    @commands.command(name="guilds", aliases=['servers', 'gm', 'sm'])
    @commands.bot_has_permissions(**_PERMS)
    async def gm_root(self, ctx: commands.Context):
        """Shows a nice list of your bot's servers."""
        group_commands = sum([1 for n in self.bot.walk_commands() if isinstance(n, type(commands.group))])

        e = discord.Embed(
            title=f"You have: {len(self.bot.guilds)}."
        )
        e.add_field(
            name="All Statistics:",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Channels:** {len(list(self.bot.get_all_channels()))}\n"
                  f"**Users:** {len(self.bot.users)}\n"
                  f"**Emojis:** {len(set(self.bot.emojis))}\n"
                  f"\n"
                  f"**Loaded Cogs:** {len(self.bot.cogs)}\n"
                  f"**Loaded Extensions:** {len(self.bot.extensions)}\n"
                  f"\n"
                  f"**Total single commands:** {len(self.bot.commands)}\n"
                  f"**Total group commands:** {group_commands}\n"
                  f"**Total sub commands:** {sum([1 for n in self.bot.walk_commands() if n.parent])}"
        )
        paginator = PaginatorEmbedInterface(
            self.bot,
            commands.Paginator(
                "", "",
                max_size=1990
            )
        )
        for n, guild in enumerate(self.bot.guilds):
            await paginator.add_line(f"{n}. {guild} (`{guild.id}`): {guild.member_count}")
        await paginator.send_to(ctx.channel)


def setup(bot):
    bot.add_cog(GuildManager(bot))