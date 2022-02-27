import calendar
import datetime

import discord
import textract
import requests
import re as regex

import _menu
import _reference

INPUTS = {
    "currentsession": "Current Session Calendar",
    "currentterm": "Current Term Calendar",
    "current": "Currnet Term Calendar",
    "nextsession": "Next Session Calendar",
    "nextterm": "Next Term Calendar",
    "next": "Next Term Calendar",
    "term1": "Term 1 Calendar",
    "term2": "Term 2 Calendar",
    "break": "Next Break Period",
    "exams": "Exam Period",
    "finals": "Exam Period"
}


def get_calendar(ctx, section) -> discord.Embed:
    url = "https://www.calendar.ubc.ca/okanagan/pdf/UBC_Okanagan_Calendar_Dates_and_Deadlines.pdf"
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        embed = discord.Embed(title="Unable to Retrive Calendar",
                              description=f"Error type: {response.status_code}",
                              color=discord.Color.red())
        embed.add_field(name="URL Used", value=url)
        return embed
    with open("calendar.pdf", 'wb') as f:
        f.write(response.content)
    pdf_text = str(textract.process("calendar.pdf"))
    text = regex.sub(r'[^A-Za-z0-9 \-,./\\():]', '', pdf_text) \
        .replace("\\xe2\\x80\\x93", "-")
    lines = list(filter(lambda a: a != "", text.split("\\n")))
    ok_calendar = {}
    for i, line in enumerate(lines):
        if "withdrawal" in line.lower():
            break
        elif "summer session" in line.lower():
            ok_calendar[lines[i][15:]] = get_session(i, lines)
        elif "winter session" in line.lower():
            ok_calendar[lines[i][15:]] = get_session(i, lines, summer=False)
    today = datetime.datetime.today().astimezone(_menu.est)
    year = today.year
    next_year = (today + datetime.timedelta(days=365)).year
    month_current = today.strftime("%B")
    months = _reference.MONTHS
    months.update({item[1]: item[0] for item in months.items()})
    current_session, current_term, next_session, next_term = {}, {}, {}, {}
    for session in ok_calendar.keys():
        for term in ok_calendar[session]:
            period = regex.search(r"\((.*?)\)", term.replace(",", "")).group()
            month_start = regex.search(r"\([^ -]*", period).group()[1:]
            month_end = regex.search(r"- (.*)[A-Za-z]", period).group()[2:]
            term_year = regex.search(r"(\d+)(?!.*\d)", period).group()
            if term_year == str(year) and current_term == {}:
                start_index = months[month_start[:3]]
                end_index = months[month_end[:3]]
                current_index = months[month_current[:3]]
                if start_index <= current_index <= end_index:
                    current_session = session
                    current_term = term
                elif current_term != {} and current_index >= end_index:
                    next_term = term
            elif term_year == str(next_year) or term_year == str(year):
                next_session = session
                if next_term == {}:
                    next_term = term
                break
    student_calendar = {
        "current": (current_term, ok_calendar[current_session][current_term]),
        "currentterm": (current_term, ok_calendar[current_session][current_term]),
        "currentsession": (current_session, ok_calendar[current_session])
    }
    if next_session != {}:
        student_calendar["nextsession"] = (next_session, ok_calendar[next_session])
    if next_term in ok_calendar[current_session].keys():
        student_calendar["next"] = (next_term, ok_calendar[current_session][next_term])
        student_calendar["nextterm"] = (next_term, ok_calendar[current_session][next_term])
    else:
        if "nextsession" in student_calendar.keys():
            student_calendar["next"] = (next_term, ok_calendar[next_session][next_term])
            student_calendar["nextterm"] = (next_term, ok_calendar[next_session][next_term])
        else:
            student_calendar["next"] = "No Info"
            student_calendar["nextterm"] = "No Info"
    if "Midterm Break" in ok_calendar[current_session][current_term]:
        break_period = ok_calendar[current_session][current_term]["Midterm Break"]
        first_day = int(regex.search(r"[0-9]+ -", break_period).group()[:-2])
        last_day = int(regex.search(r"(\d+)(?!.*\d)", break_period).group())
        break_month = months[break_period[:3]]
        current_month = months[month_current[:3]]
        if current_month < break_month or (break_month == current_month and today.day <= last_day):
            start_weekday = calendar.day_name[datetime.datetime(year, break_month, first_day).weekday()]
            end_weekday = calendar.day_name[datetime.datetime(year, break_month, last_day).weekday()]
            student_calendar["break"] = ("Midterm Break",
                                         f"{start_weekday}, {calendar.month_name[break_month]} {first_day} to "
                                         f"{end_weekday}, {calendar.month_name[break_month]} {last_day}")
    if "break" not in student_calendar.keys():
        term_end = ok_calendar[current_session][current_term]["Exams Finish"]
        term_start = student_calendar["next"][1]["Start"]
        student_calendar["break"] = ("Term Break", f"{term_end} to {term_start}")
    terms = list(ok_calendar[current_session].keys())
    student_calendar["term1"] = (terms[0], ok_calendar[current_session][terms[0]])
    student_calendar["term2"] = (terms[1], ok_calendar[current_session][terms[1]])
    exam_start = ok_calendar[current_session][current_term]["Exams Start"]
    exam_end = ok_calendar[current_session][current_term]["Exams Finish"]
    student_calendar["exams"] = ("Final Exams", f"{exam_start} to {exam_end}")
    student_calendar["finals"] = ("Final Exams", f"{exam_start} to {exam_end}")
    embed = discord.Embed(title=INPUTS[section], color=discord.Color.purple())
    try:
        name = student_calendar[section][0]
    except KeyError:
        embed.description = "**No Information Found** \n\n" \
                            "Full Academic Calendar Here: \n " \
                            "https://www.calendar.ubc.ca/okanagan/pdf/UBC_Okanagan_Calendar_Dates_and_Deadlines.pdf "
        return embed
    if section in ["currentsession", "nextsession"]:
        embed.description = f"**{name}**"
        for term_key in student_calendar[section][1].keys():
            term = student_calendar[section][1][term_key]
            embed.add_field(name="\u200b", value=f"**{term_key}**", inline=False)
            for sub_key in term.keys():
                embed.add_field(name=sub_key, value=term[sub_key])
    elif section in ["currentterm", "current", "nextterm", "next", "term1", "term2"]:
        embed.description = f"**{name}**"
        term = student_calendar[section][1]
        for sub_key in term.keys():
            embed.add_field(name=sub_key, value=term[sub_key])
    elif section in ["break", "exams", "finals"]:
        embed.add_field(name=name, value=student_calendar[section][1])
    return embed


def get_session(i, lines, summer=True) -> dict:
    dates = {
        f"{lines[i + 1]} {lines[i + 2]}": {
            lines[i + 5]: lines[i + 6],
            lines[i + 8]: lines[i + 9],
            lines[i + 11]: lines[i + 12],
            lines[i + 14]: lines[i + 15],
            lines[i + 17]: lines[i + 18]
        },
        f"{lines[i + 3]} {lines[i + 4]}": {
            lines[i + 5]: lines[i + 7],
            lines[i + 8]: lines[i + 10],
            lines[i + 11]: lines[i + 13],
            lines[i + 14]: lines[i + 16],
            lines[i + 17]: lines[i + 19]
        }
    }
    if not summer:
        dates[f"{lines[i + 1]} {lines[i + 2]}"][lines[i + 20]] = lines[i + 21]
        dates[f"{lines[i + 3]} {lines[i + 4]}"][lines[i + 20]] = lines[i + 22]
    return dates
