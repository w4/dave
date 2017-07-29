# -*- coding: utf-8 -*-
"""Give the user back urbandictionary results."""
import dave.module
import dave.config
import requests
import pickle
import re
from urllib.parse import quote_plus
from twisted.words.protocols.irc import assembleFormattedText, attributes as A


@dave.module.help("Get results for an urbandictionary query. Syntax: urban [result #] (query)")
@dave.module.command(["urbandictionary", "ub", "urban"], "(\d+ )?([a-zA-Z0-9 ]+)$")
@dave.module.priority(dave.module.Priority.HIGHEST)
def urbandictionary(bot, args, sender, source):
    result = int(args[0].strip()) - 1 if args[0] else 0
    query = args[1].strip().lower()

    key = "urban:{}:{}".format(query, result)

    if dave.config.redis.exists(key):
        bot.reply(source, sender, dave.config.redis.get(key).decode('utf-8'))
        return

    if not dave.config.redis.exists("urban_query:{}".format(query)):
        url = "https://mashape-community-urban-dictionary.p.mashape.com/define?term={}".format(quote_plus(query))
        r = requests.get(url, headers={
            "X-Mashape-Key": dave.config.config["api_keys"]["mashape"],
            "Accept": "text/plain"
        })

        resp = r.json()
        dave.config.redis.setex("urban_query:{}".format(query), 86400, pickle.dumps(resp))
    else:
        resp = pickle.loads(dave.config.redis.get("urban_query:{}".format(query)))

    print(resp)

    if len(resp["list"]) > result:
        res = resp["list"][result]
        definition = re.sub(r"\r?\n|\r", "", res["definition"].strip())

        if len(definition) > 200:
            definition = definition[:197] + "..."

        definition = assembleFormattedText(A.normal[A.bold[str(res["word"])], ": {} [by {}, 👍 {} 👎 {}] [more at {}]".format(
            definition,
            res["author"],
            res["thumbs_up"],
            res["thumbs_down"],
            res["permalink"]
        )])

        dave.config.redis.setex(key, 86400, definition)
        bot.reply(source, sender, definition)
    else:
        bot.reply(source, sender, "There are no entries for: {} at position {}".format(
            query,
            result
        ))
