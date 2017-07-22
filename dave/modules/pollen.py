# -*- coding: utf-8 -*-
"""Get the pollen count for a UK postcode."""
import dave.module
from bs4 import BeautifulSoup
from requests import get
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
import dave.config


@dave.module.help("Syntax: pollen [first part of postcode]. Get the forecast in the specified location. Only works for UK postcodes.")
@dave.module.command(["pollen"], "(([gG][iI][rR] {0,}0[aA]{2})|((([a-pr-uwyzA-PR-UWYZ][a-hk-yA-HK-Y]?[0-9][0-9]?)|(([a-pr-uwyzA-PR-UWYZ][0-9][a-hjkstuwA-HJKSTUW])|([a-pr-uwyzA-PR-UWYZ][a-hk-yA-HK-Y][0-9][abehmnprv-yABEHMNPRV-Y])))))$")
@dave.module.priority(dave.module.Priority.HIGHEST)
def pollen(bot, args, sender, source):
    postcode = args[0].lower()

    text = None

    if not dave.config.redis.exists("pollen:{}".format(postcode)):
        res = get("https://www.bbc.co.uk/weather/{}".format(postcode))

        soup = BeautifulSoup(res.text, "html.parser")
        element = soup.find_all("div", class_="environmental-index pollen-index")

        if element:
            pollen = element[0].find("span")

            if pollen:
                text = pollen.text
                dave.config.redis.setex("pollen:{}".format(postcode), 1800, text)
    else:
        text = dave.config.redis.get("pollen:{}".format(postcode))

    if text:
        bot.reply(source, sender, assembleFormattedText(
            A.normal["The pollen count is currently ", A.bold[str(text)], " in ", postcode.upper()]
        ))
