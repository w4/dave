import pickle

import dave.module
import dave.config
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
from requests import get
from humanize import naturaltime, intcomma
from datetime import datetime, timezone
import isodate

BASE_URL = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet," \
           "statistics&key={}".format(dave.config.config["api_keys"]["youtube"])

@dave.module.match(r'.*https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-\_]*)(&(amp;)?[\w\=]*)?.*')
@dave.module.dont_always_run_if_run()
def youtubevideo(bot, args, sender, source):
    """Ran whenever a YouTube video is sent"""
    if not dave.config.redis.exists("youtube:{}".format(args[0])):
        req = get("{}&id={}".format(BASE_URL, args[0]),
                  headers={'user-agent': 'irc bot (https://github.com/w4)'})

        if req.status_code != 200:
            bot.msg(source, "Bad response from YouTube API: {}".format(req.status_code))
            return

        req = req.json()

        if not req["pageInfo"]["totalResults"]:
            bot.msg(source, "That video doesn't exist.")
            return

        dave.config.redis.setex("youtube:{}".format(args[0]), 400,
                                pickle.dumps(req))
    else:
        req = pickle.loads(dave.config.redis.get("youtube:{}".format(args[0])))

    resp = req["items"][0]

    bot.msg(source, assembleFormattedText(
        A.normal[
            A.bold[resp["snippet"]["title"]],
            " ({}) by {} uploaded {}. {} views, 👍 {} 👎 {}.".format(
                str(isodate.parse_duration(resp["contentDetails"]["duration"])),
                resp["snippet"]["channelTitle"],
                naturaltime(
                    datetime.now(timezone.utc)
                        - isodate.parse_datetime(resp["snippet"]["publishedAt"])
                ),
                intcomma(resp["statistics"]["viewCount"]),
                intcomma(resp["statistics"]["likeCount"]),
                intcomma(resp["statistics"]["dislikeCount"])
            )
        ]
    ))