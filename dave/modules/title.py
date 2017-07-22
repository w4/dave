# -*- coding: utf-8 -*-
"""Get the title from a link using BeautifulSoup."""
import re
import dave.module
from bs4 import BeautifulSoup
from mechanize import Browser
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
import dave.config
import socket

parse = re.compile(r"(?:(?:https?):\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,}))\.?)(?::\d{2,5})?(?:[/?#]\S*)?", re.IGNORECASE)


@dave.module.match(r"(.*)")
@dave.module.always_run()
def link_parse(bot, args, sender, source):
    matches = parse.findall(args[0])

    br = Browser()
    br.set_handle_robots(False)

    titles = []

    for match in matches:
        if not dave.config.redis.exists("site:{}".format(match)):
            res = br.open(match)
            data = res.get_data()

            soup = BeautifulSoup(data, "html.parser")
            title = soup.title

            if title is not None:
                title = re.sub(r"\r?\n|\r",
                               "",
                               title.string.encode("utf-8").strip())
                dave.config.redis.setex("site:{}".format(match), 300, title)
        else:
            title = dave.config.redis.get("site:{}".format(match))

        if title is not None:
            titles.append(assembleFormattedText(A.bold[title]))

    if titles:
        bot.msg(source, "Linked: {}".format(
                        assembleFormattedText(A.normal[" | "]).join(titles)))
