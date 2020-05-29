import subprocess

from discord.ext import commands
from discord.ext.commands import Converter

def get_git_commit():
    string = ""
    try:
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            string += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            string += '+g' + out.decode('utf-8').strip()
    finally:
        return string


class Guild(Converter):
    """
    A converter designed to convert a given input into a guild.

    Conversion logic:
        1. name in guild name or guild name in name
        2. guild id = provided argument
        3. channel id in guild
    """
    async def convert(self, ctx, argument):
        """Converts into a discord.Guild."""
        for guild in ctx.bot.guilds:
            if guild.name.lower() in argument.lower() or argument.lower() in guild.name.lower():
                return guild
            elif str(guild.id) == argument:
                return guild
            elif argument in [str(x.id) for x in guild.channels]:
                return guild
        raise commands.BadArgument(f"Unable to convert \"{argument}\" to discord.Guild.")