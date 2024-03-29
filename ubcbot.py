#!/Users/benjamin/.pyenv/shims/python
import asyncio
import re
import traceback
from threading import Thread

from discord.ext.commands import has_permissions

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

    thread = Thread(target=_menu.between_callback, args=(asyncio.get_event_loop(),))
    thread.start()
    # await _menu.send_daily_menu()
    # _menu.generate_menu(True, "4")


@client.event
async def on_message(message):
    await client.wait_until_ready()
    if message.author == client.user:
        return
    if _config.item_to_add:
        if f"<@!{message.author.id}>" == _config.current_editor:
            if isinstance(message.channel, discord.DMChannel):
                await _config.process_item(message)
    await client.process_commands(message)


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.nick != after.nick:
        locked_names = _reference.get_file("locked_names")
        if str(before.id) in locked_names.keys():
            await after.edit(nick=locked_names[str(before.id)])


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
    # if selected_input is None:
    #     _config.inaccurate_button_view = discord.ui.View(timeout=None)
    #     _config.config_button = discord.ui.Button(label="Inaccurate?", style=discord.ButtonStyle.blurple, emoji="🔧")
    #     _config.config_button.callback = _config.config_button_callback
    #     _config.inaccurate_button_view.add_item(_config.config_button)
    #     _config.menu_message_channel = ctx.channel
    #     _config.menu_message = await ctx.send(embed=embed, view=_config.inaccurate_button_view)
    # else:
    await ctx.send(embed=embed)
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


# <!-- locknickname --!>
@client.command()
@has_permissions(manage_nicknames=True)
async def locknickname(ctx, mention, *name):
    name = " ".join(name)
    if mention is None or "<@" not in mention:
        await ctx.send(embed=discord.Embed(title="Lock Nickname Error", description="A user mention is required"))
        return
    elif "<@&" in mention:
        await ctx.send(embed=discord.Embed(title="Lock Nickname Error", description="Mention cannot be a role"))
        return
    if name is None:
        await ctx.send(embed=discord.Embed(title="Lock Nickname Error", description="A nickname is required"))
        return
    user_id = int(re.findall(r'\d+', mention)[0])
    guild: discord.Guild = client.get_guild(ctx.guild.id)
    user: discord.Member = guild.get_member(user_id)
    try:
        await user.edit(nick=name)
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(title="Lock Nickname Error",
                                           description=f"I don't have the required permissions to set <@{user_id}>'s nickname"))
        return
    locked_names = _reference.get_file("locked_names")
    locked_names[user_id] = name
    _reference.save_file("locked_names", locked_names)
    await ctx.send(embed=discord.Embed(title="Lock Nickname", description=f"<@{user_id}>'s nickname has been locked to {name}"))


@client.command()
@has_permissions(manage_nicknames=True)
async def unlocknickname(ctx, mention):
    if mention is None or "<@" not in mention:
        await ctx.send(embed=discord.Embed(title="Lock Nickname Error", description="A user mention is required"))
        return
    user_id = re.findall(r'\d+', mention)[0]
    locked_names = _reference.get_file("locked_names")
    locked_names.pop(user_id, None)
    _reference.save_file("locked_names", locked_names)
    await ctx.send(embed=discord.Embed(title="Lock Nickname", description=f"<@{user_id}>'s nickname has been unlocked"))
# <!-- locknickname --!>


# <!-- history --!>
@client.command()
@has_permissions(administrator=True)
async def history(ctx, limit=5):
    history_json = _reference.get_file("history")
    embed = discord.Embed(title="Menu Change History")
    display = ""
    entries = list(history_json.keys())
    entries.reverse()
    i = 0
    for timestamp in entries:
        name = list(history_json[timestamp].keys())[0]
        added = history_json[timestamp][name]['added']
        removed = history_json[timestamp][name]['removed']
        changed = history_json[timestamp][name]['database_edit']
        display += f"{name}\n"
        if added:
            display += f" - added: {added}\n"
        if removed:
            display += f" - removed: {removed}\n"
        if changed:
            display += f" - db_added: {changed}\n"
        i += 1
        if i == limit + 1:
            break
    embed.description = display
    await ctx.send(embed=embed)


@history.error
async def history_error(ctx, error):
    if ctx.author.id == 430678754931507201:
        await history(ctx)
        return
    embed = discord.Embed(title="History Error", description="You do not have permission to view menu edit history", color=discord.Color.red())
    await ctx.send(embed=embed)
# <!-- history --!>


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
