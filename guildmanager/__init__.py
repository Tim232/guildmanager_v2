import json
import logging

import discord
from discord.ext import commands, tasks
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

__version__ = "0.0.3a"


class GuildManager(commands.Cog):
    """
    A modular cog to help with guild management on discord.py bots.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.pings = 0.0
        self.average_latency = float(self.bot.latency / 1000)

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
        finally:
            logging.info("[GUILDMANAGER] Cog Loaded.")
            self.sample_ping.start()

    def cog_unload(self):
        logging.info(f"[GUILDMANAGER] Cog unloaded.")
        self.sample_ping.stop()

    async def cog_check(self, ctx: commands.Context):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()

        return True

    @property
    def ping(self) -> float:
        """Returns the bot's average latency (heartbeat/api connection latency), in ms.

        This is sampled every second."""
        return self.average_latency

    @property
    def sampled_pings(self) -> float:
        """returns how many times the cog has sampled pings."""
        return self.pings

    @tasks.loop(seconds=1)
    async def sample_ping(self):
        """
        Samples pings every second.
        **Do NOT overwrite this!**
        """
        self.pings += 1
        latency = self.bot.latency / 1000  # convert to ms
        self.average_latency += latency
        self.average_latency /= self.pings

    @commands.command(name="guilds", aliases=['servers', 'gm', 'sm'])
    @commands.bot_has_permissions(**_PERMS)
    async def gm_root(self, ctx: commands.Context):
        """Shows a nice list of your bot's servers."""
        group_commands = sum([1 for n in self.bot.walk_commands() if isinstance(n, commands.Group)])

        e = discord.Embed(
            title=f"You have: {len(self.bot.guilds)}."
        )
        e.add_field(
            name="All Statistics:",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Channels:** {len(list(self.bot.get_all_channels()))}\n"
                  f"**Users:** {len(self.bot.users)}\n"
                  f"**Emojis:** {len(set(self.bot.emojis))}\n"
                  f"**Cached Messages:** {len(self.bot.cached_messages)}\n"
                  f"**Average Ping:** `{round(self.average_latency, 3)}ms`\n"
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
            ),
            embed=e
        )
        for n, guild in enumerate(self.bot.guilds):
            await paginator.add_line(f"{n}. {guild} (`{guild.id}`): {guild.member_count}")
        await paginator.send_to(ctx.channel)


def setup(bot):
    bot.add_cog(GuildManager(bot))