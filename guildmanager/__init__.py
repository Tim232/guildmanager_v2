import argparse
import io
import json
import logging
import typing
from datetime import datetime
from typing import Union

import discord
import psutil
from discord.ext import commands, tasks
from humanize import naturaltime as nt, intcomma as ic
from jishaku.paginators import PaginatorEmbedInterface
from jishaku.shell import ShellReader
from matplotlib import pyplot as plt

from .helpers import get_git_commit, Guild

_DEFAULTS = {
    "banned": []
}
_PERMS = {
    "read_messages": True,
    "send_messages": True,
    "embed_links": True,
    "attach_files": True,
    "manage_messages": True,
    "add_reactions": True,
    "use_external_emojis": True
}

__version__ = "0.0.4a"
__git_ver__ = get_git_commit()

parser = argparse.ArgumentParser()  # soonTM

def percent(part: float, whole: float = 100.0, *, r: int = 0) -> float:
    """Calculates percentages. Now't special."""
    if part == 0 or whole == 0:
        part += 0.00000000001
        whole += 0.00000000001
    return round((part / whole) * 100, r)


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
        with open("./gman.data", "w") as wfile:
            json.dump(self.data, wfile)
        logging.info(f"[GUILDMANAGER] Cog unloaded.")
        self.sample_ping.stop()

    async def cog_check(self, ctx: commands.Context):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()

        return True

    async def bot_check(self, ctx):
        if ctx.guild:
            if ctx.guild.id in self.data.get("banned", []):
                raise commands.CheckFailure("This server is prohibited from using this bot. Please contact the owner"
                                            " to have this lifted.")
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
        latency = self.bot.latency * 1000
        latency = latency / self.pings
        self.average_latency = latency

    @commands.group(name="guilds", aliases=['servers', 'gm', 'sm'], invoke_without_command=True)
    @commands.bot_has_permissions(**_PERMS)
    async def gm_root(self, ctx: commands.Context):
        """Shows a nice list of your bot's servers."""
        group_commands = sum([1 for n in self.bot.walk_commands() if isinstance(n, commands.Group)])

        e = discord.Embed(
            title=f"You have: {len(self.bot.guilds)} guilds."
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
        e.add_field(name="Cog Info", value=f"**Loaded:** {nt(self.loaded)}\n"
                                           f"**Sampled Pings:** {ic(self.sampled_pings)}\n"
                                           f"**Version:** {__version__}")

        owners = [x.owner for x in self.bot.guilds]
        v = ""
        sorted_ = sorted(set(owners), key=lambda x: percent(owners.count(x), len(owners)), reverse=True)
        for n, user in enumerate(list(sorted_)[:10], start=1):
            v += f"{n}. {user} ({percent(owners.count(user), len(owners))}%)\n"
        e.add_field(name="Guild owners, sorted by number of servers they own that uses the bot:", value=v)

        paginator = PaginatorEmbedInterface(
            self.bot,
            commands.Paginator(
                "", "",
                max_size=1990
            ),
            embed=e
        )
        for n, guild in enumerate(self.bot.guilds):
            await paginator.add_line(f"{ic(n)}. {guild} (`{guild.id}`): {guild.member_count}")
        await paginator.send_to(ctx.channel)

    @gm_root.command(name="invite")
    async def gm_invite(self, ctx: commands.Context, *, guild: Guild):
        """Tries to get an invite from a guild.

        Logic is as follows:
            1. get invites
            if that fails:
            2. generate a temp invite
            if that fails
            3. cry"""
        guild: discord.Guild
        if "VANITY_URL" in guild.features:
            i = await guild.vanity_invite()
            return await ctx.send(f"Vanity Invite: <{i.url}>", delete_after=10)
        if guild.me.guild_permissions.manage_guild:
            m = await ctx.send("Attempting to find an invite.")
            invites = await guild.invites()
            for invite in invites:
                if invite.max_age == 0:
                    return await m.edit(content=f"Infinite Invite: {invite}")
            else:
                await m.edit(content="No Infinite Invites found - creating.")
                for channel in guild.text_channels:
                    try:
                        invite = await channel.create_invite(max_age=60, max_uses=1, unique=True,
                                                             reason=f"Invite requested"
                                                                    f" by {ctx.author} via official management command. "
                                                                    f"do not be alarmed, this is usually just"
                                                                    f" to check something.")
                        break
                    except:
                        continue
                else:
                    return await m.edit(content=f"Unable to create an invite - missing permissions.")
                await m.edit(content=f"Temp invite: {invite.url} -> max age: 60s, max uses: 1")
        else:
            m = await ctx.send("Attempting to create an invite.")
            for channel in guild.text_channels:
                try:
                    invite = await channel.create_invite(max_age=60, max_uses=1, unique=True, reason=f"Invite requested"
                                                                                                     f" by {ctx.author} via official management command. do not be alarmed, this is usually just"
                                                                                                     f" to check something.")
                    break
                except:
                    continue
            else:
                return await m.edit(content=f"Unable to create an invite - missing permissions.")
            await m.edit(content=f"Temp invite: {invite.url} -> max age: 60s, max uses: 1")

    @gm_root.command(name="leave", aliases=['rem', 'remove'])
    async def gm_leave(self, ctx: commands.Context, *, guild: Guild):
        """Leaves a server."""
        guild: discord.Guild
        await guild.leave()
        return await ctx.message.add_reaction("\N{white heavy check mark}")

    @gm_root.command(name="mutual", aliases=['in'])
    async def gm_mutual(self, ctx: commands.Context, *, user: Union[discord.Member, discord.User, int]):
        """Tells you how many mutual guilds the bot has with another user."""
        if isinstance(user, int): return await ctx.send("User not found.")
        paginator = commands.Paginator("```md")
        n = 1
        r = 0
        for n, guild in enumerate(self.bot.guilds, start=1):
            if user in guild.members:
                paginator.add_line(f"{n}. {guild.name}")
                r += 1
        if len(paginator.pages) == 0:
            return await ctx.send(f"`0` mutual guilds.")
        else:
            await ctx.send(f"`{n}` mutual guilds:\n{paginator.pages[0]}")
            if len(paginator.pages) >= 2:
                for page in paginator.pages[1:]:
                    await ctx.send(page)

    @gm_root.command(name="update")
    async def update(self, ctx, *, version: str = None):
        """Updates the module to the latest (or provided) version."""
        proc = psutil.Process()
        with proc.oneshot():
            command = proc.name()
            if not command.lower().startswith("py"):
                return await ctx.send(f"Unable to automatically update: process name does not start with `py`,"
                                      f" so unable to invoke pip.")
            else:
                run = command.lower() + " -m pip install guildmanager-v2" + (" --upgrade" if not version else f"=={version}")

        paginator = PaginatorEmbedInterface(self.bot, commands.Paginator("```bash", "```", 1600))
        async with ctx.channel.typing():
            with ShellReader(run, 120) as reader:
                async for line in reader:
                    if paginator.closed:
                        return
                    else:
                        await paginator.add_line(line)
                await paginator.add_line(f"[status] return code {reader.close_code}")
        return await paginator.send_to(ctx.channel)

    @gm_root.command(name="search", aliases=['find', 'query'])
    async def gm_find(self, ctx: commands.Context, *, q: typing.Union[discord.User, int, str]):
        """Iterates through bot.guilds, and if `q` is equal to owner, ID, or name, matches.

        For a more in-depth version of this, like checking channel/role names, etc, use `[p]guilds get`."""
        if isinstance(q, discord.User):
            matches = []
            for guild in self.bot.guilds:
                if guild.owner == q:
                    matches.append(guild)
                    continue
            if len(matches) == 0:
                return await ctx.send(f"No matches.")
            else:
                pc = percent(len(matches), len(self.bot.guilds), r=2)
                paginator = commands.Paginator("```md", max_size=1800)
                for n, match in enumerate(matches, start=1):
                    paginator.add_line(f"{n}. {match.name} ({match.id})")

                first_page = f"{q.mention} owns {pc}% of the bot's servers:\n{paginator.pages[0]}"
                await ctx.send(first_page)
                if len(paginator.pages) > 1:
                    for page in paginator.pages: await ctx.send(page)
        elif isinstance(q, int):
            matches = []
            for guild in self.bot.guilds:
                if guild.owner.id == q or guild.id == q:
                    matches.append(guild)
                    continue
            if len(matches) == 0:
                return await ctx.send(f"No matches.")
            else:
                pc = percent(len(matches), len(self.bot.guilds), r=2)
                paginator = commands.Paginator("```md", max_size=1800)
                for n, match in enumerate(matches, start=1):
                    paginator.add_line(f"{n}. {match.name} ({match.id})")

                first_page = paginator.pages[0]
                await ctx.send(first_page)
                if len(paginator.pages) > 1:
                    for page in paginator.pages: await ctx.send(page)
        else:
            matches = []
            for guild in self.bot.guilds:
                if guild.name.lower() in q.lower() or q.lower() in guild.name.lower():
                    matches.append(guild)
                    continue
            if len(matches) == 0:
                return await ctx.send(f"No matches.")
            else:
                pc = percent(len(matches), len(self.bot.guilds), r=2)
                paginator = commands.Paginator("```md", max_size=1800)
                for n, match in enumerate(matches, start=1):
                    paginator.add_line(f"{n}. {match.name} ({match.id})")

                first_page = paginator.pages[0]
                await ctx.send(first_page)
                if len(paginator.pages) > 1:
                    for page in paginator.pages: await ctx.send(page)

    @gm_root.command(name="growth", aliases=['graph'])
    async def gm_growth(self, ctx: commands.Context):
        """Shows your growth statistics, in a neat little graph!"""
        plt.clf()
        guilds = [
            guild.me.joined_at for guild in self.bot.guilds
        ]
        guilds.sort(key=lambda g: g)
        plt.grid(True)
        fig, ax = plt.subplots()

        ax.plot(guilds, tuple(range(len(guilds))), lw=2)

        fig.autofmt_xdate()

        plt.xlabel('Date')
        plt.ylabel('Guilds')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        e = discord.Embed(color=discord.Color.orange())
        e.set_image(url="attachment://attachment.png")
        return await ctx.send(embed=e, file=discord.File(buf, "attachment.png"))

    @gm_root.command(name="ban")
    async def ban(self, ctx: commands.Context, leave_too: typing.Optional[bool] = False, *, guild: Guild):
        """Bans a server from using the bot

        if `leave_too` is True, this will leave the server after banning it.
        If it is not, the bot will just not respond to any commands in that server (but will raise checkfailures)."""
        # prevent a softlock with no obvious fix to people with less than 1 braincell
        owner_in = list(
            filter(lambda g: ctx.author in g.members and g.id not in self.data.get('banned', []) and g.id != guild.id,
                   self.bot.guilds))
        if len(owner_in) <= 0:
            return await ctx.send(f"Unable to ban as this would softlock the bot.")
        else:
            if not self.data.get("banned"):
                self.data["banned"] = [guild.id]
            else:
                self.data["banned"].append(guild.id)
            return await ctx.send(f"\N{white heavy check mark} banned the server {guild.id}.")

    @gm_root.command(name="unban")
    async def gm_unbn(self, ctx: commands.Context, *, guild: typing.Union[Guild, int]):
        """Unbans a server. See: [p]help guilds ban"""
        if isinstance(guild, discord.Guild): guild = guild.id
        if not self.data.get("banned"):
            self.data["banned"] = []
        else:
            self.data["banned"].remove(guild)
        return await ctx.send(f"\N{white heavy check mark} unbanned the server {guild}.")


def setup(bot):
    bot.add_cog(GuildManager(bot))