#!/usr/local/bin/python3.9
import traceback

import _reference
import _menu
import _calendar
import _config
import discord
from _menu import get_display, get_weekly_menu
from _calendar import get_calendar
from _reference import client, TOKEN_MEE6
from _config import Button, View


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
    embed = await get_message(ctx, selected_input)
    if selected_input is None:
        config_button = Button(label="Inaccurate?", style=discord.ButtonStyle.blurple, emoji="🔧")
        view = View()
        view.add_item(config_button)
        config_button.callback = _config.config_button_callback
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(embed=embed)


async def get_message(ctx, selected_input) -> discord.Embed:
    if selected_input is None:
        selected_input = "today"
    weekly_menu = get_weekly_menu()
    embed = discord.Embed(title=_menu.INPUTS[selected_input],
                          color=discord.colour.Colour.blue())
    result = get_display(weekly_menu, selected_input)
    display = result[0]
    if result[1] is not None:
        dm_embed = result[1]
        user = client.get_user(ctx.author.id)
        if user is None:
            user = await client.fetch_user(ctx.author.id)
        channel = user.dm_channel
        if channel is None:
            channel = await user.create_dm()
        await channel.send(embed=dm_embed)
    embed.description = display
    if "error" in weekly_menu.keys():
        embed.set_footer(text="Last Week's Menu - Pritchard Hasn't Updated Their Menu Yet")
    return embed


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
