from discord.ext import commands
import discord
import json
import _menu

intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', intents=intents)
client.remove_command('help')

with open(".token.txt") as file:
    content = file.readlines()

TOKEN = content[0]
TOKEN_MEE6 = content[1]

MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}


async def get_message(ctx, selected_input) -> discord.Embed:
    if selected_input is None:
        selected_input = "today"
    weekly_menu = await _menu.get_weekly_menu(ctx, selected_input)
    if selected_input == "-1":
        selected_input = "today"
    embed = discord.Embed(title=_menu.INPUTS[selected_input],
                          color=discord.colour.Colour.blue())
    result = _menu.get_display(weekly_menu, selected_input)
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


def validate_input(args, inputs) -> tuple[str, discord.Embed]:
    selected_input = None
    embed = None
    if args is not None:
        user_input = args
        valid_input = False
        for e in inputs.keys():
            if user_input == e:
                selected_input = user_input
                valid_input = True
        if not valid_input:
            if args == "list" or args == "help":
                embed = discord.Embed(title="Avaliable Inputs: ",
                                      description="{}".format(", ".join(inputs)),
                                      color=discord.colour.Colour.blue())
            else:
                embed = discord.Embed(title="Input Error",
                                      description="Avaliable Inputs: {}".format(", ".join(inputs)),
                                      color=discord.colour.Colour.red())
    return selected_input, embed


def save_file(name, settings):
    with open('{}.json'.format(name), 'w') as f:
        json.dump(settings, f, indent=4)


def get_file(name):
    with open('{}.json'.format(name), 'r') as f:
        return json.load(f)
