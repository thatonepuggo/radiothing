import os
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands import Context
from discord import Interaction, app_commands
import discord
from typing import Literal, Optional

import api

from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client = commands.Bot(command_prefix='+', intents=intents)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
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


@client.command(description='Syncs bot commands.')
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: Context, guilds: commands.Greedy[discord.Object],
               spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


@client.command(description="Play a radio station.")
async def play(ctx: Context, *, args: str):
    source, channel_id = search_one(args)
    channel = ctx.message.author.voice.channel
    print(source)
    if channel:
        vc = await channel.connect()
        vc.play(discord.FFmpegPCMAudio(api.listen_url(channel_id)))
        await ctx.reply(f"now playing: {source['title']} - {source['subtitle']} (please wait)")

@client.event
async def on_ready():
    await client.tree.sync(guild=discord.Object(id=458771009135443998))
    print(f"Logged in as {client.user.name}!")


#@client.event
#async def on_command_error(ctx: Context, error):
#    if isinstance(error, commands.CommandNotFound):
#        await ctx.reply("Command not found!")
#    else:
#        await ctx.reply(f"AGGESFGACH!!\n```\nAn error occurred:\n{str(error)}\n```")


if __name__ == '__main__':
    client.run(os.environ['DISCORD_TOKEN'])
