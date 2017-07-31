# -*- coding: utf-8 -*-
"""Get the title from a link using BeautifulSoup."""
import re
import dave.module
from bs4 import BeautifulSoup
from requests import get
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
import dave.config
from twisted.python import log

parse = re.compile(r"(?:(?:https?):\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,}))\.?)(?::\d{2,5})?(?:[/?#]\S*)?", re.IGNORECASE)

@dave.module.match(r"(.*)")
@dave.module.always_run()
@dave.module.ratelimit(2, 2)
def link_parse(bot, args, sender, source):
    matches = parse.findall(args[0])

    titles = []

    for match in matches:
        if not dave.config.redis.exists("site:{}".format(match)):
            try:
                res = get(match, timeout=3,
                          headers={'user-agent': 'irc bot (https://github.com/w4)'})
            except BaseException as e:
                log.msg("Couldn't connect to host.", e)
                return

            # sometimes requests guesses the charset wrong
            if res.encoding == 'ISO-8859-1' and not 'ISO-8859-1' in \
                    res.headers.get('Content-Type', ''):
                res.encoding = res.apparent_encoding

            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.title.string

            if title is not None:
                title = re.sub(r"(\r?\n|\r| )+",
                               " ",
                               title.strip())
                title = title[:140] + (title[140:] and '...')
                dave.config.redis.setex("site:{}".format(match), 300, title)
        else:
            title = str(dave.config.redis.get("site:{}".format(match)), 'utf8')

        if title is not None:
            titles.append(assembleFormattedText(A.bold[title]))

    if titles:
        # remove duplicates
        titles = list(set(titles))

        bot.msg(source, "Title: {}".format(
                        assembleFormattedText(A.normal[", "]).join(titles)))
