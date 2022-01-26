import datetime

from docx2pdf import convert
import subprocess
import discord
import textract
import re as regex
import glob
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
DAY_NUMS = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
}


def get_display(weekly_menu, selected_input, today) -> tuple[str, discord.Embed]:
    display = ""
    dm_embed = None
    if selected_input == "today":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n*{}*\n- {}" \
            .format(INPUTS["chefbr"],
                    "\n- ".join(weekly_menu["chefbr"][DAY_NUMS[today.weekday()]]),
                    INPUTS["chef"],
                    "\n- ".join(weekly_menu["chef"][DAY_NUMS[today.weekday()]]),
                    INPUTS["pizza&pasta"],
                    "\n- ".join(weekly_menu["pizza&pasta"][DAY_NUMS[today.weekday()]]),
                    INPUTS["grill"],
                    "\n- ".join(weekly_menu["grill"][DAY_NUMS[today.weekday()]]),
                    INPUTS["nourish"],
                    "".join(weekly_menu["nourish_message"]),
                    "\n- ".join(weekly_menu["nourish"][DAY_NUMS[today.weekday()]]))
    elif selected_input == "daily":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("All Day",
                    "\n- ".join(weekly_menu["daily"]["all day"]),
                    "Breakfast",
                    "\n- ".join(weekly_menu["daily"]["breakfast"]),
                    "Lunch and Dinner",
                    "\n- ".join(weekly_menu["daily"]["lunch and dinner"]))
    elif selected_input == "chef":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["chef"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["chef"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["chef"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["chef"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["chef"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["chef"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["chef"]["sunday"]))
    elif selected_input == "chefbr":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["chefbr"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["chefbr"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["chefbr"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["chefbr"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["chefbr"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["chefbr"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["chefbr"]["sunday"]))
    elif selected_input == "pizza&pasta":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["sunday"]))
    elif selected_input == "grill":
        display = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["grill"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["grill"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["grill"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["grill"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["grill"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["grill"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["grill"]["sunday"]))
    elif selected_input == "nourish":
        display = "*{}*\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("".join(weekly_menu["nourish_message"]),
                    "Monday",
                    "\n- ".join(weekly_menu["nourish"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["nourish"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["nourish"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["nourish"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["nourish"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["nourish"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["nourish"]["sunday"]))
    elif selected_input == "full":
        display = "Full Menu sent in direct messages"
        dm_embed = discord.Embed(title=INPUTS[selected_input],
                                 color=discord.colour.Colour.blue())
        grill = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["grill"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["grill"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["grill"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["grill"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["grill"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["grill"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["grill"]["sunday"]))
        pizzapasta = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["pizza&pasta"]["sunday"]))
        chef = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["chef"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["chef"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["chef"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["chef"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["chef"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["chef"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["chef"]["sunday"]))
        chefbr = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("Monday",
                    "\n- ".join(weekly_menu["chefbr"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["chefbr"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["chefbr"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["chefbr"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["chefbr"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["chefbr"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["chefbr"]["sunday"]))
        nourish = "*{}*\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}\n**{}**\n- " \
                  "{}" \
            .format("".join(weekly_menu["nourish_message"]),
                    "Monday",
                    "\n- ".join(weekly_menu["nourish"]["monday"]),
                    "Tuesday",
                    "\n- ".join(weekly_menu["nourish"]["tuesday"]),
                    "Wednesday",
                    "\n- ".join(weekly_menu["nourish"]["wednesday"]),
                    "Thursday",
                    "\n- ".join(weekly_menu["nourish"]["thursday"]),
                    "Friday",
                    "\n- ".join(weekly_menu["nourish"]["friday"]),
                    "Saturday",
                    "\n- ".join(weekly_menu["nourish"]["saturday"]),
                    "Sunday",
                    "\n- ".join(weekly_menu["nourish"]["sunday"]))
        daily = "**{}**\n- {}\n**{}**\n- {}\n**{}**\n- {}" \
            .format("All Day",
                    "\n- ".join(weekly_menu["daily"]["all day"]),
                    "Breakfast",
                    "\n- ".join(weekly_menu["daily"]["breakfast"]),
                    "Lunch and Dinner",
                    "\n- ".join(weekly_menu["daily"]["lunch and dinner"]))
        dm_embed.add_field(name="> **Chef's Table Breakfast**", value=chefbr, inline=False)
        dm_embed.add_field(name="> **Chef's Table Dinner**", value=chef, inline=False)
        dm_embed.add_field(name="> **Pizza and Pasta (Lunch / Dinner)**", value=pizzapasta, inline=False)
        dm_embed.add_field(name="> **The Grill (Lunch / Dinner)**", value=grill, inline=False)
        dm_embed.add_field(name="> **Nourish (Lunch)**", value=nourish, inline=False)
        dm_embed.add_field(name="> **Every day**", value=daily, inline=False)
    return display, dm_embed


def convert_to_pdf(path):
    convert(path, path[:-5] + ".pdf", True)
    os.system("killall \"Microsoft Word\"")
    return path[:-5] + ".pdf"


def get_weekly_menu(today) -> dict:
    monday = (today - datetime.timedelta(days=today.weekday()))
    sunday = monday + datetime.timedelta(days=6)
    months = _reference.MONTHS
    attempts = []
    url = f"https://food.ok.ubc.ca/wp-content/uploads/{monday.year}/{monday.month:02d}/Pritchard-Menu-{months[monday.month].upper()}-{monday.day}-{sunday.day}-{sunday.year}.pdf"
    url2 = f"https://food.ok.ubc.ca/wp-content/uploads/{monday.year}/{monday.month:02d}/Pritchard-Menu-{months[monday.month].upper()}-{monday.day}-{months[sunday.month]}.-{sunday.day}-{sunday.year}.pdf"
    url3 = f"https://food.ok.ubc.ca/wp-content/uploads/{monday.year}/{monday.month:02d}/Pritchard-Menu-{months[monday.month].upper()}-{monday.day}-{sunday.day}.docx"
    current_menu_file = f"./cache/{monday.year}_{monday.month}_Pritchard-Menu-{months[monday.month]}.-{monday.day}-{sunday.day}-{sunday.year}.pdf"
    attempts.append(url)
    attempts.append(url2)
    attempts.append(url3)
    weekly_menu = {}
    url_used = None
    if not os.path.isfile(current_menu_file):
        response = None
        for attempt in attempts:
            response = requests.get(attempt, stream=True)
            if response.status_code == 200:
                url_used = attempt
                break
        if response.status_code == 404:
            weekly_menu["error"] = 404
        elif response.status_code == 200:
            if url_used == url3:
                current_menu_file = current_menu_file[:-4] + ".docx"
                with open(current_menu_file, 'wb') as f:
                    f.write(response.content)
                current_menu_file = convert_to_pdf(current_menu_file)
            else:
                with open(current_menu_file, 'wb') as f:
                    f.write(response.content)
    if "error" in weekly_menu.keys():
        file_list = glob.glob("./cache/*")
        current_menu_file = max(file_list, key=os.path.getctime)
    pdf_text = str(textract.process(current_menu_file))
    text = regex.sub(r'[^A-Za-z \\():]', '', pdf_text) \
        .replace("\\xe\\x\\x", "\'") \
        .replace("\\xc", "") \
        .replace("\\no Add", " with optional") \
        .replace("madewithoutgluten", "made without gluten") \
        .replace("plantbased", "plant based") \
        .replace("Applebraised", "Apple braised") \
        .replace("Appleglazed", "Apple glazed")
    lines = text.split("\\n")
    lines.append("END")
    for i in range(len(lines)):
        line = lines[i]
        if line.lower() == "chef's table dinner":
            result = get_day_dishes(i, lines, "PIZZA  PASTA LUNCHDINNER")
            weekly_menu["chef"] = result[0]
            i += result[1]
        if line.lower() == "chef's table breakfast":
            result = get_day_dishes(i, lines, "NOURISH LUNCH")
            weekly_menu["chefbr"] = result[0]
            i += result[1]
        elif line.lower() == "pizza  pasta lunchdinner":
            result = get_day_dishes(i, lines, "GRILL LUNCHDINNER")
            weekly_menu["pizza&pasta"] = result[0]
            i += result[1]
        elif line.lower() == "grill lunchdinner":
            result = get_day_dishes(i, lines, "CHEF'S TABLE BREAKFAST")
            weekly_menu["grill"] = result[0]
            i += result[1]
        elif line.lower() == "nourish lunch":
            result = get_day_dishes(i, lines, "AVAILABLE EVERY DAY: ALL DAY")
            weekly_menu["nourish"] = result[0]
            weekly_menu["nourish_message"] = "E" + weekly_menu["nourish"]["friday"].pop()
            i += result[1]
        elif "every day" in line.lower():
            weekly_menu["daily"] = get_daily_dishes(i, lines)
            break
    return weekly_menu


def get_daily_dishes(index, lines) -> dict:
    line = lines[index]
    daily_dishes = {"breakfast": [], "lunch and dinner": [], "all day": []}
    selected = ""
    while line != "END":
        if "all day" in line.lower():
            selected = "all day"
            changed = True
        elif "breakfast" in line.lower():
            selected = "breakfast"
            changed = True
        elif "lunch and dinner" in line.lower():
            selected = "lunch and dinner"
            changed = True
        else:
            changed = False
        if line != "" and not changed:
            if "made without gluten" not in line:
                daily_dishes[selected].append(lines[index])
        index += 1
        line = lines[index]
    return daily_dishes


def get_day_dishes(index, lines, end) -> tuple[dict, int]:
    line = lines[index]
    day_dishes = {"monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [],
                  "sunday": []}
    current_day = ""
    skip_count = 0
    days = list(DAY_NUMS.values())
    while line != end:
        if line.lower() in days:
            try:
                day_index = days.index(current_day)
            except ValueError:
                day_index = -1
            current_day = days[day_index + 1]
        elif current_day != "":
            day_dishes[current_day].append(line[1:])
        index += 1
        skip_count += 1
        line = lines[index]
    if not day_dishes.get('saturday'):
        day_dishes.get('friday').pop()
        day_dishes['saturday'] = ["Not Open"]
        day_dishes['sunday'] = ["Not Open"]
    else:
        day_dishes.get('sunday').pop()
    return day_dishes, skip_count
