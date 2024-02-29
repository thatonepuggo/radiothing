import os
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
from discord.ext.commands import Command
from discord.ext.commands import Context
from discord.colour import Color
import discord
from typing import Literal, Optional

import api

from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client = commands.Bot(command_prefix='+', intents=intents)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
channels = {}

# https://stackoverflow.com/questions/4092528/how-can-i-clamp-clip-restrict-a-number-to-some-range
def clamp(n, smallest, largest): return max(smallest, min(n, largest))


def search_one(query):
    search_results = api.search(query)['hits']['hits']
    highest_score = 0
    pick_id = ""
    source = {}

    for i in search_results:
        source = i['_source']
        score = i['_score']
        # print(source['title'] + ": " + source['type'] + ' ' + source['url'])
        if source['type'] == "channel":
            print(f"{source['title']}: {score}")
            if score >= highest_score:
                highest_score = score
                pick_id = api.get_id(source['url'])
    return source, pick_id

def perm_check(ctx: Context, runner):
    return runner == ctx.author.id or ctx.channel.permissions_for(ctx.author).manage_channels


async def vc_play(ctx: Context, vc: discord.VoiceClient, source, channel_id):
    if not vc.is_connected():
        return False
    vc.play(FFmpegPCMAudio(api.listen_url(channel_id)))
    await ctx.reply(f"now playing: {source['title']} from station {source['subtitle'] if 'subtitle' in source else ':person_shrugging:'} (please wait)")

@client.command(description="play a radio station.")
async def play(ctx: Context, *, args: str):
    source, channel_id = search_one(args)
    channel = ctx.message.author.voice.channel

    if not source:
        await ctx.reply("no results")
        return
    
    if not channel:
        await ctx.reply("please join a voice channel")
        return
    print(source)

    if channel.id not in channels.keys():
        vc = await channel.connect()
        channels[channel.id] = {"vc": vc, "author": ctx.author.id, "volume": 1}
        await vc_play(ctx, vc, source, channel_id)
    else:
        vc: discord.VoiceClient = channels[channel.id]["vc"]
        channels[channel.id]["author"] = ctx.author.id
        vc.stop()

@client.command(description="stop the radio.")
async def stop(ctx: Context):
    channel = ctx.message.author.voice.channel

    if not channel:
        await ctx.reply("please join a voice channel")
        return

    if channel.id not in channels.keys():
        await ctx.reply(f"not in <#{channel.id}>!")
        return

    vc: discord.VoiceClient = channels[channel.id]["vc"]
    runner = channels[channel.id]["author"]
    
    if not perm_check(ctx, runner):
        await ctx.reply("you do not have permissions to stop the radio.")
        return

    await vc.disconnect()
    del channels[channel.id]


# @client.command(description="change the volume (0-1).")
# async def vol(ctx: Context, volume: float):
#     channel = ctx.message.author.voice.channel
#
#     if channel.id not in channels:
#         await ctx.reply(f"not in <#{channel.id}>!")
#         return
#
#     runner = channels[channel.id]["author"]
#
#     if not perm_check(ctx, runner):
#         await ctx.reply("you do not have permissions to change the volume of the radio.")
#         return
#
#     volume = clamp(volume, 0, 1)
#     channels[channel.id]["volume"] = volume


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

    @staticmethod
    def description_append(cmd: Command):
        if cmd.name == "help":
            return f'- show this message.'
        if cmd.description:
            return f'- {cmd.description}'
        return ''

    def command_not_found(self, string):
        return f":x: **Command **'{string}'** not found.**"

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return f":x: **Command **'{command.qualified_name}'** has no subcommand named **'{string}'**.**"
        return f":x: **Command **'{command.qualified_name}'** has no subcommands.**"

    def add_bot_commands_formatting(self, cmds, heading):
        if cmds:
            joined = '\n'.join(f'**{c.name}** {self.description_append(c)}' for c in cmds)
            self.paginator.add_line(f'__**{heading}**__')
            self.paginator.add_line(joined)


client.help_command = MyHelpCommand()

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}!")


#@client.event
#async def on_command_error(ctx: Context, error):
#    if isinstance(error, commands.CommandNotFound):
#        await ctx.reply("Command not found!")
#    else:
#        await ctx.reply(f"AGGESFGACH!!\n```\nAn error occurred:\n{str(error)}\n```")


if __name__ == '__main__':
    client.run(os.environ['DISCORD_TOKEN'])
