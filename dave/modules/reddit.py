"""Return some useful reddit info"""
import pickle
from datetime import datetime

import dave.module
import dave.config
import uuid
import random
from dave.models import Quote
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
from requests import get
from humanize import naturaltime

@dave.module.match(r'(?:https?://(?:www\.)?reddit.com)?(/r/(.+)/comments/([^\s]+))')
@dave.module.match(r'https?://(?:www\.)?redd.it/([^\s]+)')
@dave.module.dont_always_run_if_run()
def post(bot, args, sender, source):
    """Ran whenever a reddit post is sent"""
    if not dave.config.redis.exists("reddit:post:{}".format(args[0])):
        req = get("https://reddit.com/{}.json".format(args[0]),
                  headers={'user-agent': 'irc bot (https://github.com/w4)'})

        if req.status_code != 200:
            bot.send(source, responsestatus(req.status_code, "That post"))
            return

        req = req.json()

        dave.config.redis.setex("reddit:post:{}".format(args[0]), 200,
                                pickle.dumps(req))
    else:
        req = pickle.loads(dave.config.redis.get("reddit:post:{}".format(args[0])))

    resp = req[0]["data"]["children"][0]["data"]

    bot.msg(source, assembleFormattedText(
        A.normal[
            A.lightred["[NSFW] "] if resp["over_18"] else "",
            A.bold[resp["title"][:75] + (resp["title"][75:] and '...')],
            " by ", A.bold[resp["author"]],
            " (/r/{}) {} comments, {} points, posted {}".format(
                resp["subreddit"],
                resp["num_comments"],
                resp["score"],
                naturaltime(datetime.utcnow().timestamp() - resp["created_utc"])
            ),
        ]
    ))

def responsestatus(status, item):
    if status == 404:
        out = "{} does not exist.".format(item)
    elif status == 403:
        out = "{} is private.".format(item)
    elif status == 429:
        out = "Rate-limited by reddit. Please try again in a few minutes."
    else:
        out = "Reddit returned an error, response: {}".format(status)

    return out
