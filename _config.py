from __future__ import annotations
from discord.ui import Button, View, Select
from discord import SelectOption
import discord
import datetime
import _reference
import _menu

current_editor = ""
menu_message_channel = None
innacurate_button_view: None | View = None
menu_message: None | discord.Message = None
option_message: None | discord.Message = None
config_message: None | discord.Message = None
json_menu: dict = {}
saved_menu: dict = {}
weekday: int = -1


async def remove_button_callback(interaction: discord.Interaction):
    removed_id = interaction.data["custom_id"]
    selection = removed_id[0]
    index = int(removed_id[-1])
    json_menu[selection][str(weekday)].pop(index)
    await present_options(interaction, selection)


async def add_option_menu_callback(interaction: discord.Interaction):
    selection = interaction.data["values"][0]
    stand = selection[0]
    day = selection[2]
    index = int(selection[4])
    option = saved_menu[stand][day][index]
    json_menu[stand][str(weekday)].append(option)
    await present_options(interaction, stand)


async def cancel_button_callback(interaction: discord.Interaction):
    global option_message
    global current_editor
    if option_message is not None:
        await option_message.delete()
    await config_message.delete()
    option_message = None
    current_editor = ""


async def save_button_callback(interaction: discord.Interaction):
    global option_message
    global current_editor
    global menu_message
    history: dict = _reference.get_file("history")
    user: discord.User = interaction.user
    added = []
    removed = []
    for stand in json_menu.keys():
        if stand == "day_created":
            continue
        for day in json_menu[stand]:
            if day == "nourish_message":
                continue
            for option in json_menu[stand][day]:
                if option not in saved_menu[stand][day]:
                    added.append(option)
            for option in saved_menu[stand][day]:
                if option not in json_menu[stand][day]:
                    removed.append(option)
    if "actions" not in history:
        history["actions"] = []
    history["actions"].append(
        f"{user.name}:(added:{added}, removed:{removed})"
    )
    _reference.save_file("history", history)
    _reference.save_file("menu_store", json_menu)
    if option_message is not None:
        await option_message.delete()
    await config_message.delete()
    embed = await _reference.get_message(menu_message_channel, None)
    menu_message = await menu_message.edit(embed=embed, view=innacurate_button_view)
    option_message = None
    current_editor = ""


async def present_options(interaction, selection):
    global option_message
    current_options = json_menu[selection][str(weekday)]

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
    add_option_menu = Select(options=possible_options, placeholder="Add Menu Item")
    add_option_menu.callback = add_option_menu_callback
    view.add_item(add_option_menu)

    save_button = Button(label="Save", style=discord.ButtonStyle.green, row=2)
    save_button.callback = save_button_callback
    view.add_item(save_button)

    embed.description = display
    if i == 0:
        embed.description = "Stand Empty"
    if option_message is None:
        option_message = await channel.send(embed=embed, view=view)
    else:
        option_message = await option_message.edit(embed=embed, view=view)


async def select_menu_callback(interaction: discord.Interaction):
    selection = interaction.data["values"][0]
    await present_options(interaction, selection)


async def config_button_callback(interaction: discord.Interaction):
    global json_menu
    global weekday
    global config_message
    global current_editor
    global saved_menu
    dm_channel = interaction.user.dm_channel
    if dm_channel is None:
        dm_channel = await interaction.user.create_dm()

    if current_editor != "":
        embed = discord.Embed(title="Configure Menu", description=f"Currently being edited by {current_editor}")
        await dm_channel.send(embed=embed)
        return

    current_editor = interaction.user.name

    json_menu = _reference.get_file("menu_store")
    saved_menu = _reference.get_file("menu_archive")
    today = datetime.date.today()
    weekday = today.weekday()

    today_menu = {}
    for key in json_menu.keys():
        if str(weekday) in json_menu[key]:
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
                                                              f"2. Remove or add dishes to the stand\n"
                                                              f"3. Save the menu to update what .menu shows or cancel", color=discord.Color.yellow())
    config_message = await dm_channel.send(embed=embed, view=view)
