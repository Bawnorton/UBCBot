from __future__ import annotations

import asyncio
from typing import Union

from discord.ui import Button, View, Select
from discord import SelectOption
from threading import Thread
import discord
import datetime
import _reference
import _menu

menu_message_channel = None

inaccurate_button_view: None | View = None

config_button: None | Button = None

menu_message: None | discord.Message = None
option_message: None | discord.Message = None
config_message: None | discord.Message = None
add_option_message: None | discord.Message = None
confirm_message: None | discord.Message = None

current_editor: str = ""
process_item_stand: str = "-1"
item_to_add: bool = False
removed: list[str] = []
added: list[str] = []
json_menu: dict = {}
saved_menu: dict = {}
weekday: int = -1
time_editing: int = 0


async def counter():
    global time_editing
    while time_editing <= 180:
        if current_editor == "":
            return
        time_editing += 1
        await asyncio.sleep(1)
    await cancel_button_callback(None)


def between_callback(loop):
    loop.create_task(counter())


async def remove_button_callback(interaction: discord.Interaction):
    removed_id = interaction.data["custom_id"]
    selection = removed_id[0]
    index = int(removed_id[2:])
    removed_option = json_menu[selection][str(weekday)].pop(index)
    removed.append(removed_option)
    await present_options(interaction, selection)


async def process_item_confirm_button_callback(interaction: discord.Interaction):
    added_item = interaction.data["custom_id"].capitalize()
    saved_menu[process_item_stand][str(weekday)].append(added_item)
    _reference.save_file("menu_archive", saved_menu)

    history_json = _reference.get_file("history")
    username = f"<@!{interaction.user.id}>"
    now = str(datetime.datetime.now())
    history_json[now] = {}
    history_json[now][username] = {}
    history_json[now][username]["added"] = []
    history_json[now][username]["removed"] = []
    history_json[now][username]["database_edit"] = f"\"{_menu.positions.inverse[int(process_item_stand)]}: {added_item}\""
    _reference.save_file("history", history_json)

    await confirm_message.delete()
    await add_option_message.delete()
    await present_options(interaction, process_item_stand)


async def process_item_cancel_button_callback(interaction: discord.Interaction):
    await confirm_message.delete()
    await add_option_message.delete()
    await present_options(interaction, process_item_stand)


async def process_item(message):
    global confirm_message
    item = message.content
    embed = discord.Embed(title="Item to Add", description=f"\"{item}\"\nThis will appear in the menu edit history", color=discord.Color.yellow())

    view = View()
    confirm_button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id=item)
    confirm_button.callback = process_item_confirm_button_callback
    view.add_item(confirm_button)

    cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red)
    cancel_button.callback = process_item_cancel_button_callback
    view.add_item(cancel_button)

    confirm_message = await message.channel.send(embed=embed, view=view)


async def add_option_to_list(stand, interaction: discord.Interaction):
    global item_to_add, add_option_message, process_item_stand
    embed = discord.Embed(title="Add Menu Item",
                          description=f"Next message sent will be what is added to the {_menu.positions.inverse[int(stand)]} stand",
                          color=discord.Color.yellow())
    process_item_stand = stand
    channel = interaction.channel
    add_option_message = await channel.send(embed=embed)
    item_to_add = True


async def add_option_menu_callback(interaction: discord.Interaction):
    selection = interaction.data["values"][0]
    stand = selection[0]
    day = selection[2]
    if day == "n":
        await add_option_to_list(stand, interaction)
        return
    try:
        try:
            await add_option_message.delete()
            await confirm_message.delete()
        except discord.NotFound:
            pass
    except AttributeError:
        pass
    index = int(selection[4:])
    option = saved_menu[stand][day][index]
    added.append(option)
    json_menu[stand][str(weekday)].append(option)
    await present_options(interaction, stand)


async def cancel_button_callback(interaction: None | discord.Interaction):
    global option_message, current_editor, time_editing
    if option_message is not None:
        await option_message.delete()
    await config_message.delete()
    option_message = None
    current_editor = ""
    time_editing = 0


async def save_button_callback(interaction: discord.Interaction):
    global option_message, current_editor, menu_message, time_editing, added, removed
    _reference.save_file("menu_store", json_menu)
    for entry in added:
        if entry in removed:
            added.remove(entry)
            removed.remove(entry)
    if added != [] and removed != []:
        history_json = _reference.get_file("history")
        username = f"<@!{interaction.user.id}"
        now = str(datetime.datetime.now())
        history_json[now] = {}
        history_json[now][username] = {}
        history_json[now][username]["added"] = added
        history_json[now][username]["removed"] = removed
        history_json[now][username]["database_edit"] = []
        _reference.save_file("history", history_json)
        added = []
        removed = []
    if option_message is not None:
        await option_message.delete()
    await config_message.delete()
    embed = await _reference.get_message(menu_message_channel, "-1")
    menu_message = await menu_message.edit(embed=embed, view=inaccurate_button_view)
    option_message = None
    current_editor = ""
    time_editing = 0


async def present_options(interaction, selection):
    global option_message, time_editing
    current_options = json_menu[selection][str(weekday)]
    time_editing = 0

    channel = interaction.user.dm_channel
    embed = discord.Embed(title=_menu.positions.inverse[int(selection)])
    view = View()
    i = 0
    display = ""
    for option in current_options:
        display += f"{i + 1}: {option}\n"
        remove_button = Button(label=f"Remove {i + 1}", style=discord.ButtonStyle.red, custom_id=f"{selection}:{i}")
        i += 1
        view.add_item(remove_button)
        remove_button.callback = remove_button_callback

    possible_options: list[SelectOption] = []
    shown_lables = []
    for day in saved_menu[selection]:
        j = 0
        if day == "nourish_message":
            continue
        for option in saved_menu[selection][day]:
            if option not in current_options and option not in shown_lables:
                shown_lables.append(option)
                possible_options.append(
                    SelectOption(label=option, value=f"{selection}:{day}:{j}")
                )
            j += 1
    possible_options.append(SelectOption(label="Add Item to List", value=f"{selection}:n"))
    add_option_menu = Select(options=possible_options, placeholder="Add Menu Item")
    add_option_menu.callback = add_option_menu_callback
    view.add_item(add_option_menu)

    save_button = Button(label="Save", style=discord.ButtonStyle.green, row=2)
    save_button.callback = save_button_callback
    view.add_item(save_button)

    embed.description = display
    if i == 0:
        embed.description = "Stand Empty"
    elif i == 5:
        view.remove_item(add_option_menu)
    if option_message is None:
        option_message = await channel.send(embed=embed, view=view)
    else:
        option_message = await option_message.edit(embed=embed, view=view)


async def select_menu_callback(interaction: discord.Interaction):
    selection = interaction.data["values"][0]
    await present_options(interaction, selection)


async def config_button_callback(interaction: discord.Interaction):
    global json_menu, weekday, config_message, current_editor, saved_menu
    dm_channel = interaction.user.dm_channel
    if dm_channel is None:
        dm_channel = await interaction.user.create_dm()

    if current_editor != "":
        embed = discord.Embed(title="Configure Menu", description=f"Currently being edited by {current_editor}")
        await dm_channel.send(embed=embed)
        return

    current_editor = f"<@!{interaction.user.id}>"
    thread = Thread(target=between_callback, args=(asyncio.get_event_loop(),))
    thread.start()

    json_menu = _reference.get_file("menu_store")
    saved_menu = _reference.get_file("menu_archive")
    today = datetime.date.today()
    weekday = today.weekday()

    today_menu = {}
    for key in json_menu.keys():
        if str(weekday) in json_menu[key]:
            if key == "day_created" or key == "menu_url":
                continue
            today_menu[key] = json_menu[key][str(weekday)]

    select_options: list[SelectOption] = []
    for key in today_menu.keys():
        select_options.append(
            SelectOption(label=_menu.positions.inverse[int(key)], value=key)
        )
    view = View()
    select_menu = Select(options=select_options, placeholder="Choose a Stand")
    select_menu.callback = select_menu_callback
    view.add_item(select_menu)

    cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    cancel_button.callback = cancel_button_callback
    view.add_item(cancel_button)

    embed = discord.Embed(title="Configure Menu", description=f"1. Select which stand to configure{' '}from the select menu below\n"
                                                              f"2. Remove or add dishes to the stand (Can't be more than 5)\n"
                                                              f"    - Option to \"Add Item to List\" at the bottom of select menu\n"
                                                              f"3. Save the menu to update what .menu shows or cancel", color=discord.Color.yellow())
    config_message = await dm_channel.send(embed=embed, view=view)


