#!/Users/benjamin/.pyenv/shims/python
import asyncio
import traceback
from threading import Thread

import _reference
import _menu
import _calendar
import _config
import discord
from _calendar import get_calendar
from _reference import client, TOKEN_MEE6


@client.event
async def on_ready():
    print("online")
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, name=".help"))


@client.event
async def on_message(message):
    await client.wait_until_ready()
    if message.author == client.user:
        return
    await client.process_commands(message)


# <!-- help --!>
@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help",
                          color=discord.Color.green())
    embed.add_field(name="menu", value="Get menu from pritchard\n.menu help")
    embed.add_field(name="calendar", value="Get academic calendar\n.calendar help")
    await ctx.send(embed=embed)
# <!-- help --!>


# <!-- menu --!>
@client.command()
async def menu(ctx, args=None):
    value = _reference.validate_input(args, _menu.INPUTS)
    if value[1] is not None:
        await ctx.channel.send(embed=value[1])
        return
    selected_input = value[0]
    embed = await _reference.get_message(ctx, selected_input)
    if selected_input is None:
        _config.inaccurate_button_view = discord.ui.View()
        _config.config_button = discord.ui.Button(label="Inaccurate?", style=discord.ButtonStyle.blurple, emoji="🔧", custom_id="config_button")
        _config.inaccurate_button_view.add_item(_config.config_button)
        _config.menu_message_channel = ctx.channel
        _config.menu_message = await ctx.send(embed=embed, view=_config.inaccurate_button_view)
    else:
        await ctx.send(embed=embed)


@client.event
async def on_interaction(interaction: discord.Interaction):
    custom_id = interaction.data["custom_id"]
    if custom_id == "config_button":
        await _config.config_button_callback(interaction)
# <!-- menu --!>


# <!-- calendar --!>
@client.command()
async def calendar(ctx, args=None):
    value = _reference.validate_input(args, _calendar.INPUTS)
    if value[1] is not None:
        await ctx.channel.send(embed=value[1])
        return
    selected_input = value[0]
    if selected_input is None:
        selected_input = "current"
    embed = get_calendar(ctx, selected_input)
    await ctx.send(embed=embed)
# <!-- calendar --!>


@menu.error
@calendar.error
async def runtime_error(ctx, error):
    embed = discord.Embed(title="Internal Error", description="Sent DM to #Bawnorton0001")
    embed.set_footer(text="Do not fret, I promise I know what I'm doing :P")
    await ctx.send(embed=embed)
    guild = ctx.guild
    if guild is None:
        guild_name = f"#{ctx.author.name}{ctx.author.discriminator}"
        channel_name = "DM"
    else:
        guild_name = guild.name
        channel_name = ctx.channel.name
    embed_error = discord.Embed(title=f"Error in {guild_name} in #{channel_name}",
                                description=f"```\n{traceback.format_exc()}\n```")
    me = client.get_user(430678754931507201)
    if me is None:
        me = await client.fetch_user(430678754931507201)
    channel = me.dm_channel
    if channel is None:
        channel = await me.create_dm()
    await channel.send(embed=embed_error)


client.run(TOKEN_MEE6)
