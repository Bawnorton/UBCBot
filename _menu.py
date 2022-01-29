from docx import Document
from bs4 import BeautifulSoup
from datetime import datetime as dt
from bidict import bidict
import datetime
import discord
import textract
import os.path
import requests

import _reference

INPUTS = {
    "today": "Today's Menu",
    "daily": "Everyday Menu",
    "chef": "Chef's Table Dinner",
    "chefbr": "Chef's Table Breakfast",
    "pizza&pasta": "Pizza and Pasta (Lunch / Dinner)",
    "grill": "The Grill (Lunch / Dinner)",
    "nourish": "Nourish (Lunch)",
    "full": "Full Menu"
}

positions: bidict[str, int] = bidict({
    "CHEF’S TABLE DINNER": 0,
    "PIZZA & PASTA LUNCH/DINNER": 1,
    "GRILL LUNCH/DINNER": 2,
    "CHEF’S TABLE BREAKFAST": 3,
    "NOURISH LUNCH": 4,
    "AVAILABLE EVERY DAY: ALL DAY": 5
})


def get_pritchard_menu_file() -> str:
    p_website = "https://food.ok.ubc.ca/places/pritchard/"
    p_response = requests.get(p_website)
    p_soup = BeautifulSoup(p_response.text, 'html.parser')

    p_menu_url: str = ""
    for url in p_soup.find_all('a'):
        link = url.get('href')
        if isinstance(link, str):
            if "Pritchard-Menu" in link:
                p_menu_url = link
                break

    if p_menu_url == "":
        raise ResourceWarning("Cannot Find Menu")

    p_menu_cache_file = f"./cache/{p_menu_url.replace('/', '-').replace('https:--food.ok.ubc.ca-wp-content-uploads-', '')}"
    if not os.path.isfile(p_menu_cache_file):
        p_menu = requests.get(p_menu_url)
        with open(p_menu_cache_file, 'wb') as file:
            file.write(p_menu.content)
    return p_menu_cache_file


def get_menu_as_list():
    file_path = get_pritchard_menu_file()
    file_type = file_path.rpartition('.')[-1]
    lines: list[str] = []

    if "pdf" in file_type:
        pdf = str(textract.process(file_path)) \
            .replace("\\xe2\\x80\\x99", "\'").replace("\\x0c", "").replace("- ", "").replace("-", "").replace("b'", '')
        lines = pdf.split("\\n")
    elif "docx" in file_type:
        document = Document(file_path)
        docx_paragraphs = []
        for paragraph in document.paragraphs:
            docx_paragraphs.append(paragraph.text)
        docx_text = "\n".join(docx_paragraphs).replace("-", "")
        lines = docx_text.split("\n")

    while "" in lines:
        lines.remove("")

    return lines


def generate_menu_json():
    today = datetime.date.today()
    create_new_menu: bool = False
    json_content = _reference.get_file("menu_store")

    if "day_created" in json_content:
        day_created_str = json_content["day_created"]
        day_created = dt.fromisoformat(day_created_str)
        if not (day_created.isocalendar()[1] == today.isocalendar()[1] and day_created.year == today.year):  # not same week
            create_new_menu = True
    else:
        create_new_menu = True

    if not create_new_menu:
        return json_content

    json_content = {}

    menu_list = get_menu_as_list()

    current_position: int = -1
    current_day: int = -1

    days: dict[str, int] = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4,
        "SATURDAY": 5,
        "SUNDAY": 6,
        "AVAILABLE EVERY DAY: ALL Day": 7,
        "AVAILABLE EVERY DAY: BREAKFAST": 8,
        "AVAILABLE EVERY DAY: LUNCH AND DINNER": 9
    }

    for line in menu_list:
        changed_day = False
        for position in positions:
            if position == line.upper():
                current_position = positions[position]
                if current_position != 5:  # include Daily Menu
                    current_day = -1
                else:
                    current_day = 7
                    changed_day = True
        for day in days:
            if day == line.upper():
                current_day = days[day]
                changed_day = True

        if changed_day:  # don't include day, eg: MONDAY
            continue

        if current_position == -1 or current_day == -1:  # don't include junk info
            continue

        if str(current_position) not in json_content:  # make sure there is somewhere for data to go
            json_content[str(current_position)] = {}

        if str(current_day) not in json_content[str(current_position)]:
            json_content[str(current_position)][str(current_day)] = []

        if current_position == 4 and current_day == 4:  # don't include nourish hint in FRIDAY menu
            if "*each bowl" in line.lower():
                json_content[str(current_position)]["nourish_message"] = line
                continue

        if current_position == 5:  # don't include daily message junk
            if "*madewithout" in line.lower():
                continue

        json_content[str(current_position)][str(current_day)].append(line)

    json_content["day_created"] = today.isoformat()
    _reference.save_file("menu_store", json_content)
    return json_content


def get_display(menu, selected_input) -> tuple[str, discord.Embed]:
    today = datetime.date.today()
    choices = {
        "chef": 0,
        "pizza&pasta": 1,
        "grill": 2,
        "chefbr": 3,
        "nourish": 4,
        "daily": 5,
        "today": 6,
        "full": 7
    }
    choice = choices[selected_input]
    display, dm_embed = None, None
    if choice <= 3:
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday", "\n- ".join(menu[str(choice)]['0']),
                    "Tuesday", "\n- ".join(menu[str(choice)]['1']),
                    "Wednesday", "\n- ".join(menu[str(choice)]['2']),
                    "Thursday", "\n- ".join(menu[str(choice)]['3']),
                    "Friday", "\n- ".join(menu[str(choice)]['4']),
                    "Saturday", "\n- ".join(menu[str(choice)]['5']),
                    "Sunday", "\n- ".join(menu[str(choice)]['6']))
    elif choice == 4:
        display = "*{}*\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("".join(menu['4']["nourish_message"]),
                    "Monday", "\n- ".join(menu['4']['0']),
                    "Tuesday", "\n- ".join(menu['4']['1']),
                    "Wednesday", "\n- ".join(menu['4']['2']),
                    "Thursday", "\n- ".join(menu['4']['3']),
                    "Friday", "\n- ".join(menu['4']['4']),
                    "Saturday", "\n- ".join(["Not Open on Saturday"]),
                    "Sunday", "\n- ".join(["Not Open on Sunday"]))
    elif choice == 5:
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("All Day", "\n- ".join(menu['5']['7']),
                    "Breakfast", "\n- ".join(menu['5']['8']),
                    "Lunch and Dinner", "\n- ".join(menu['5']['9']))
    elif choice == 6:
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n{}\n- {}" \
            .format(INPUTS["chefbr"], "\n- ".join(menu['3'][str(today.weekday())]),
                    INPUTS["chef"], "\n- ".join(menu['0'][str(today.weekday())]),
                    INPUTS["pizza&pasta"], "\n- ".join(menu['1'][str(today.weekday())]),
                    INPUTS["grill"], "\n- ".join(menu['2'][str(today.weekday())]),
                    INPUTS["nourish"], "".join(menu['4']["nourish_message"]), "\n- ".join(menu['4'][str(today.weekday())]))
    elif choice == 7:
        display = "Full Menu sent in direct messages"
        dm_embed = discord.Embed(title=INPUTS[selected_input],
                                 color=discord.colour.Colour.blue())
        format_menus = []
        for i in range(0, 4):
            format_menus.append("**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}"
                                .format("Monday", "\n- ".join(menu[str(i)]['0']),
                                        "Tuesday", "\n- ".join(menu[str(i)]['1']),
                                        "Wednesday", "\n- ".join(menu[str(i)]['2']),
                                        "Thursday", "\n- ".join(menu[str(i)]['3']),
                                        "Friday", "\n- ".join(menu[str(i)]['4']),
                                        "Saturday", "\n- ".join(menu[str(i)]['5']),
                                        "Sunday", "\n- ".join(menu[str(i)]['6'])))
        nourish = "{}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("".join(menu['4']["nourish_message"]),
                    "Monday", "\n- ".join(menu['4']['0']),
                    "Tuesday", "\n- ".join(menu['4']['1']),
                    "Wednesday", "\n- ".join(menu['4']['2']),
                    "Thursday", "\n- ".join(menu['4']['3']),
                    "Friday", "\n- ".join(menu['4']['4']),
                    "Saturday", "\n- ".join(["Not Open Today"]),
                    "Sunday", "\n- ".join(["Not Open Today"]))
        daily = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("All Day", "\n- ".join(menu['5']['7']),
                    "Breakfast", "\n- ".join(menu['5']['8']),
                    "Lunch and Dinner", "\n- ".join(menu['5']['9']))
        dm_embed.add_field(name="> **Chef's Table Breakfast**", value=format_menus[3], inline=False)
        dm_embed.add_field(name="> **Chef's Table Dinner**", value=format_menus[0], inline=False)
        dm_embed.add_field(name="> **Pizza and Pasta (Lunch / Dinner)**", value=format_menus[1], inline=False)
        dm_embed.add_field(name="> **The Grill (Lunch / Dinner)**", value=format_menus[2], inline=False)
        dm_embed.add_field(name="> **Nourish (Lunch)**", value=nourish, inline=False)
        dm_embed.add_field(name="> **Every day**", value=daily, inline=False)
    return display, dm_embed


def get_weekly_menu() -> dict:
    menu = generate_menu_json()
    return menu
