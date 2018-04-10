import time
import praw
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException
import requests
import Config
from bs4 import BeautifulSoup
reddit = praw.Reddit(client_id=Config.cid,
                     client_secret=Config.secret,
                     password=Config.password,
                     user_agent=Config.agent,
                     username=Config.user)
subreddit = reddit.subreddit(Config.subreddit)
def flair(app_rating, num_installs, sub):
    inst = num_installs.split("+")
    if (inst[0] == "Couldn't"):
        return
    elif int(inst[0].replace(',', '')) <= 500:
        sub.mod.flair(text='New app', css_class=None)
    elif int(inst[0].replace(',', '')) >= 10000 and int(app_rating[0:1]) >= 4:
        sub.mod.flair(text= 'Popular app', css_class=None)
footer = """

*****

^^^[Source](https://github.com/a-ton/gpd-bot)
^^^|
^^^[Suggestions?](https://www.reddit.com/r/GPDBot/comments/7cyrfw)"""
file = open("postids.txt","a+")
file.close()
def logID(postid):
    f = open("postids.txt","a+")
    f.write(postid + "\n")
    f.close()

def crawl(s, u):
    print("Crawling...")
    page = requests.get(u).text
    store_page = BeautifulSoup(page, "html.parser")

    list_of_details = store_page.findAll(attrs={"class": "htlgb"})

	# get app name
    try:
        app_name = store_page.find("h1", class_="AHFaub").string
    except AttributeError:
        return "incorrect link"


	# get the number of downloads
    try:
        installs = list_of_details[2].string
    except AttributeError:
        installs = "  Couldn't get # of installs (probably a new app)"

	# get rating out of 5
    try:
        temp = store_page.find("div", class_="BHMmbe").string
        rating = temp + "/5"
    except TypeError:
        rating = "No ratings yet"

	# get developer name
    dev = store_page.find("a", class_="hrTbp R8zArc").string
    if dev in Config.blacklisted_devs:
        return "Sorry, deals from " + dev + " have been blacklisted.\n\nHere is the full list of blacklisted devleopers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"

	# get last update date
    updated = list_of_details[0].string

    # get size of app
    app_size = list_of_details[1].string

    # get IAP info
    IAP_info = list_of_details[7].string

    # get current price
    temp = store_page.find("meta", itemprop="price")
    current_price = temp['content']
    if current_price == "0":
        current_price = "Free"

	# get full (normal) price
    try:
        full_price = store_page.find("span", class_="LV0gI").string
    except AttributeError:
        full_price = current_price + " (can't get price in USD)"

    # find IAPs
    iap_element = store_page.find("div", class_="rxic6")
    if iap_element == None:
        IAP = "No"
    else:
        IAP = "Yes"

    # get description
    desc = store_page.find("div", jsname="sngebd").get_text()
    flair(rating, installs, submission)

    return "Info for " + app_name + ":\n\n" + "Current price (USD): " + current_price + " was " + full_price + "  \nDeveloper: " + dev + "  \nRating: " + rating + "  \nInstalls: " + installs + "  \n Size: " + app_size + "  \nLast updated: " + updated + "  \nContains IAPs: " + IAP + ", " + IAP_info + "  \nShort description: " + desc[0:400] + "...  \n\n***** \n\nIf this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."

def respond(submission):
    title_url = submission.url
    reply_text = crawl(submission, title_url)
    reply_text += footer
    if reply_text[0:6] == "Sorry,":
        submission.mod.remove()
        submission.reply(reply_text).mod.distinguish()
        print("Removed (developer blacklist): " + submission.title)
    elif reply_text == "incorrect link" + footer:
        print("INCORRECT LINK Skipping: " + submission.title)
    else:
        submission.reply(reply_text)
        submission.mod.approve()
        print("Replied to: " + submission.title)
    logID(submission.id)

while True:
    try:
        print("Initializing bot...")
        for submission in subreddit.stream.submissions():
            if submission.is_self:
                continue
            if submission.created < int(time.time()) - 86400:
                continue
            if submission.title[0:2].lower() == "[a" or submission.title[0:2].lower() == "[i" or submission.title[0:2].lower() == "[g":
                if submission.id in open('postids.txt').read():
                    continue
                for top_level_comment in submission.comments:
                    try:
                        if top_level_comment.author and top_level_comment.author.name == "GPDBot":
                            logID(submission.id)
                            break
                    except AttributeError:
                        pass
                else: # no break before, so no comment from GPDBot
                    respond(submission)
                    continue
    except (HTTPError, ConnectionError, Timeout, RequestException):
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)