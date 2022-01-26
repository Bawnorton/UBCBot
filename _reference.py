from discord.ext import commands
import discord
import json

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
