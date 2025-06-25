import discord
import logging
import requests
from bs4 import BeautifulSoup
from thefuzz import fuzz

from discord.ext import commands
from dotenv import load_dotenv
import os

from unicodedata import category

class wikiItem:
    def __init__(self, grade, name, price, release):
        self.grade = grade
        self.name = name
        self.price = price
        self.release = release

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
paginator = commands.Paginator()

wikistr = 'https://gundam.fandom.com'
Categorystr = 'https://gundam.fandom.com/wiki/Category:Gunpla'

links = []

bot = commands.Bot(command_prefix='!', intents=intents)

# @bot.event
# async def on_ready():
#     print(f"We have logged in {bot.user.name}")

# @bot.event
# async def on_member_join(member):
#     await member.channel.send(f"Hello {member.name}, welcome to the server")

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return
    else:
        if message.content.startswith("!"):
            if "=" in message.content and len(message.content.split("=")[1].strip()) >= 0 :
                get_grades()
                searchtxt = message.content.split("=")[1].strip()
                if message.content.startswith("!MG"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "Master Grade" in v['name']] ))), message)
                elif message.content.startswith("!RE"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "Reborn-One" in v['name']] ))), message)
                elif message.content.startswith("!NG"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "1/100" in v['name']] ))), message)
                elif message.content.startswith("!FM"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "Full Mech" in v['name']] ))), message)
                elif message.content.startswith("!HG"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "High Grade" in v['name'] and "1/100" not in v['name']] ))), message)
                elif message.content.startswith("!RG"):
                    await send_list(get_list(searchtxt, list(map(lambda a:a, [v['link'] for v in links if "Real Grade" in v['name']] ))), message)
                else:
                    await message.channel.send("Use command '!{Grade}={name search}' to include search name \nGrades = [ MG, RE, NG, HG ]")
            else:
                await message.channel.send("""Use command '!{Grade}={name search}' to include search name \nGrades = [ MG, RE, NG, HG ]""")

def get_list(name, list = []):
    # Making a GET request
    displaylist = []
    for link in list:
        print(link)
        r = requests.get(link)
        # Parsing the HTML
        soup = BeautifulSoup(r.content, 'html.parser')
        header = soup.find_all("th")
        if len(header) > 0:
            gradename = header[0].text if "#" not in header[0].text else header[0].text.replace("#","").strip()
            nameindex = [i for i, e in enumerate(header) if 'Model' in e.text][0]
            priceindex = [i for i, e in enumerate(header) if 'Price' in e.text or "Yen" in e.text][0]
            releaseindex = [i for i, e in enumerate(header) if 'Date' in e.text][0]
            items = soup.find_all(class_="wds-tab__content")
            itemstab = soup.find_all("tbody")

            fulllist = []
            itemtabsplit = []

            for i, item in enumerate( items if len(items) > 0 else itemstab):
                values = item.find_all("tr")
                for value in values:
                    listings = value.find_all("td")
                    for listing in listings:
                        itemtabsplit.append(listing.text.strip())
                    fulllist.append(itemtabsplit.copy())
                    itemtabsplit.clear()

            try:
                for line in fulllist:
                    if len(line) > 0:
                        if len(name) > 0:
                            wordcount = name.lower().split(" ")
                            liststr = line[1].lower().split(" ")
                            if name.lower() in line[1].lower() or len(searchString(wordcount, liststr)) >= len(wordcount):
                                displaylist.append(gradename + " | " + line[nameindex] + " | " + line[priceindex] + " | " + line[releaseindex])
                        else:
                            displaylist.append(gradename + " | " + line[nameindex] + " | " + line[priceindex] + " | " + line[releaseindex])
            except Exception as e:
                print("error", e, gradename)

    if len(displaylist) > 0 and len(displaylist) <= 40:
        output = '\n'.join(displaylist)
    elif len(displaylist) > 40:
        output = 'More than 40 results found'
    else:
        output = 'No results found'
    return output

def get_grades():
    categorypage = requests.get(Categorystr)
    # Parsing the HTML
    soup = BeautifulSoup(categorypage.content, 'html.parser')
    for cat in soup.find_all(class_ = "category-page__member"):
        for cat1 in cat.find_all("a", href=True):
            name = cat.text.strip()
            url = cat1['href']
            link = {"name": name, "link": wikistr + url}
            if not check_value_in_dict_list(links, name):
                links.append(link)
    print(links)
    return

def searchString(inputlist = [], namelist = []):
    matches = []
    for inputstr in inputlist:
        for name in namelist:
            if fuzz.ratio(inputstr, name) > 80:
                matches.append(name)
                break
    return matches

def check_value_in_dict_list(list_of_dicts, value_to_check):
    for dictionary in list_of_dicts:
        if value_to_check in dictionary.values():
            return True
    return False

async def send_list(string, message):
    paginator.clear()
    for splititem in string.splitlines():
        paginator.add_line(splititem)
    for page in paginator.pages:
        await message.channel.send(page)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)