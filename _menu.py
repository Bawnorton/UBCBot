import asyncio
import datetime

import discord
from bidict import bidict
from discord import Webhook
import aiohttp

import _reference

INPUTS = {
    "today": "Today's Menu",
    "chef": "Chef's Table Dinner",
    "chefbr": "Chef's Table Breakfast",
    "pizza": "Pizza (Lunch / Dinner)",
    "pasta": "Pasta (Lunch / Dinner)",
    "grill": "The Grill (Lunch / Dinner)",
    "grillbr": "The Grill (Breakfast)",
    "nourish": "Nourish (Lunch)",
    "full": "Full Menu"
}

positions: bidict[str, int] = bidict({
    "Chef's Table Breakfast (8am-1030am)": 0,
    "Chef's Table (5pm-930pm)": 1,
    "Pizza (1130am-3pm, 5pm-930pm)": 2,
    "Pasta (1130am-3pm, 5pm-930pm)": 3,
    "Grill House Breakfast (7-1030am)": 4,
    "Grill House (1130am-3pm, 5pm-930pm)": 5,
    "Nourish (1130am-3pm)": 6
})

last_day = datetime.datetime.today()
current_day = datetime.datetime.today()


async def day_check():
    global last_day, current_day
    while True:
        current_day = datetime.datetime.today()
        if current_day.day != last_day.day:
            last_day = current_day
            await send_daily_menu()
        await asyncio.sleep(3600)  # 1hr


def between_callback(loop):
    loop.create_task(day_check())


async def send_daily_menu():
    async with aiohttp.ClientSession() as session:
        with open(".webhook.txt", "r") as f:
            content = f.readlines()
        webhook = Webhook.from_url(content[0], session=session)
        embed = await _reference.get_message(None, None)
        await webhook.send(embed=embed, username="UBCO 2025 Webhook",
                           avatar_url="https://cdn.discordapp.com/avatars/897829450857726003/c58e8db16963e74566943d817dd79e9a.webp?size=160")


def contains_lower(s):
    for character in s:
        if character.islower():
            return True
    return False


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def end_of_month(dt):
    todays_month = dt.month
    tomorrows_month = (dt + datetime.timedelta(days=1)).month
    return True if tomorrows_month != todays_month else False


def generate_menu(do: bool):
    if not do:
        return
    with open("menu.txt", 'r') as menu_txt:
        menu_json = _reference.get_file("menu")
        lines = menu_txt.readlines()
        month_num = "2"
        if month_num not in menu_json.keys():
            menu_json[month_num] = {}
        current_day = "0"
        current_stand = ""
        for line in lines:
            line = line.strip()
            if is_int(line):
                current_day = line
                if current_day not in menu_json[month_num].keys():
                    menu_json[month_num][current_day] = {}
                continue
            if contains_lower(line):
                current_stand = line
                if current_stand not in menu_json[month_num][current_day].keys():
                    menu_json[month_num][current_day][current_stand] = []
                continue
            menu_json[month_num][current_day][current_stand].append(line)
        _reference.save_file("menu", menu_json)


def generate_menu_json():
    menu_json = _reference.get_file("menu")

    today = datetime.datetime.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)

    current_month_json = menu_json[str(monday.month)]
    next_month_json: dict | None = None
    if sunday.month > monday.month:
        next_month_json = menu_json[str(sunday.month)]

    json_content = {}

    if next_month_json is None:
        for day in range(monday.day, sunday.day + 1):
            day_json = current_month_json[str(day)]
            day -= monday.day
            for stand in day_json.keys():
                if str(positions[stand]) not in json_content.keys():
                    json_content[str(positions[stand])] = {}
                if str(day) not in json_content[str(positions[stand])].keys():
                    json_content[str(positions[stand])][str(day)] = []
                for dish in day_json[stand]:
                    json_content[str(positions[stand])][str(day)].append(dish.lower().capitalize())
    else:
        next_month = False
        stored_offset = 0
        for day_offset in range(0, 6):
            day = monday.day + day_offset
            day_json = current_month_json[str(day)]
            if next_month:
                day = sunday.day + day_offset - stored_offset
                day_json = next_month_json[str(day)]
            day = day_offset
            for stand in day_json.keys():
                if str(positions[stand]) not in json_content.keys():
                    json_content[str(positions[stand])] = {}
                if str(day) not in json_content[str(positions[stand])].keys():
                    json_content[str(positions[stand])][str(day)] = []
                for dish in day_json[stand]:
                    json_content[str(positions[stand])][str(day)].append(dish.lower().capitalize())
            if not next_month:
                next_month = end_of_month(monday + datetime.timedelta(days=day_offset))
                if next_month:
                    stored_offset = day_offset
    return json_content


def get_display(menu, selected_input) -> tuple[discord.Embed, discord.Embed]:
    today = datetime.date.today()
    choices = {
        "chefbr": 0,
        "chef": 1,
        "pizza": 2,
        "pasta": 3,
        "grillbr": 4,
        "grill": 5,
        "nourish": 6,
        "today": 7,
        "full": 8
    }
    choice = choices[selected_input]
    display, dm_embed = discord.Embed(title=INPUTS[selected_input],
                                      color=discord.colour.Colour.blue()), None
    if choice <= 5:
        display.description = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday", "\n- ".join(menu[str(choice)]['0']),
                    "Tuesday", "\n- ".join(menu[str(choice)]['1']),
                    "Wednesday", "\n- ".join(menu[str(choice)]['2']),
                    "Thursday", "\n- ".join(menu[str(choice)]['3']),
                    "Friday", "\n- ".join(menu[str(choice)]['4']),
                    "Saturday", "\n- ".join(menu[str(choice)]['5']),
                    "Sunday", "\n- ".join(menu[str(choice)]['6']))
    elif choice == 6:
        display.description = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday", "\n- ".join(menu['6']['0']),
                    "Tuesday", "\n- ".join(menu['6']['1']),
                    "Wednesday", "\n- ".join(menu['6']['2']),
                    "Thursday", "\n- ".join(menu['6']['3']),
                    "Friday", "\n- ".join(menu['6']['4']),
                    "Saturday", "\n- ".join(["Not Open on Saturday"]),
                    "Sunday", "\n- ".join(["Not Open on Sunday"]))
    elif choice == 7:
        display.add_field(name=INPUTS["chefbr"], value="- " + "\n- ".join(menu['0'][str(today.weekday())]))
        display.add_field(name=INPUTS["chef"], value="- " + "\n- ".join(menu['1'][str(today.weekday())]))
        display.add_field(name=INPUTS["pizza"], value="- " + "\n- ".join(menu['2'][str(today.weekday())]))
        display.add_field(name=INPUTS["pasta"], value="- " + "\n- ".join(menu['3'][str(today.weekday())]))
        display.add_field(name=INPUTS["grillbr"], value="- " + "\n- ".join(menu['4'][str(today.weekday())]))
        display.add_field(name=INPUTS["grill"], value="- " + "\n- ".join(menu['5'][str(today.weekday())]))
        display.add_field(name=INPUTS["nourish"], value="- " + "\n- ".join(menu['6'][str(today.weekday())]
                                                                          if today.weekday() < 5 else ["Not Open Today"]))
    elif choice == 8:
        display.description = "Full Menu sent in direct messages"
        dm_embed = discord.Embed(title=INPUTS[selected_input],
                                 color=discord.colour.Colour.blue())
        format_menus = []
        for i in range(0, 6):
            format_menus.append("**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}"
                                .format("Monday", "\n- ".join(menu[str(i)]['0']),
                                        "Tuesday", "\n- ".join(menu[str(i)]['1']),
                                        "Wednesday", "\n- ".join(menu[str(i)]['2']),
                                        "Thursday", "\n- ".join(menu[str(i)]['3']),
                                        "Friday", "\n- ".join(menu[str(i)]['4']),
                                        "Saturday", "\n- ".join(menu[str(i)]['5']),
                                        "Sunday", "\n- ".join(menu[str(i)]['6'])))
        nourish = "n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday", "\n- ".join(menu['6']['0']),
                    "Tuesday", "\n- ".join(menu['6']['1']),
                    "Wednesday", "\n- ".join(menu['6']['2']),
                    "Thursday", "\n- ".join(menu['6']['3']),
                    "Friday", "\n- ".join(menu['6']['4']),
                    "Saturday", "\n- ".join(["Not Open Today"]),
                    "Sunday", "\n- ".join(["Not Open Today"]))
        dm_embed.add_field(name="> **Chef's Table Breakfast**", value=format_menus[0], inline=False)
        dm_embed.add_field(name="> **Chef's Table Dinner**", value=format_menus[1], inline=False)
        dm_embed.add_field(name="> **Pizza (Lunch / Dinner)**", value=format_menus[2], inline=False)
        dm_embed.add_field(name="> **Pasta (Lunch / Dinner)**", value=format_menus[3], inline=False)
        dm_embed.add_field(name="> **The Grill (Breakfast)**", value=format_menus[4], inline=False)
        dm_embed.add_field(name="> **The Grill (Lunch / Dinner)**", value=format_menus[5], inline=False)
        dm_embed.add_field(name="> **Nourish (Lunch)**", value=nourish, inline=False)
    return display, dm_embed


async def get_weekly_menu() -> dict:
    return generate_menu_json()
