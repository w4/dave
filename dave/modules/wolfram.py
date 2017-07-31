# -*- coding: utf-8 -*-
"""Query the Wolfram API when the user wants to find something out."""
import dave.module
import dave.config
import wolframalpha
from twisted.words.protocols.irc import assembleFormattedText, attributes as A


@dave.module.help("Query the Wolfram API and return the result back to the user.")
@dave.module.command(["wolfram", "w", "wolframalpha", "wa"], "(.+)$")
@dave.module.priority(dave.module.Priority.HIGHEST)
@dave.module.ratelimit(1, 3)
def wolfram(bot, args, sender, source):
    query = args[0].strip()

    key = "wolfram:{}".format(query.lower())

    if dave.config.redis.exists(key):
        bot.reply(source, sender, dave.config.redis.get(key).decode('utf-8'))
        dave.config.redis.setex(key, 60, dave.config.redis.get(key))
        return

    if query:
        client = wolframalpha.Client(dave.config.config["api_keys"]["wolfram"])
        res = client.query(query)

        pods = list(res.pods)

        if len(pods) > 0:
            resultpod = next(res.results)
            result = resultpod.text

            if "image" in pods[0].text:
                result = resultpod.img

            if len(result) > 500:
                result = result[:497] + "..."

            res = assembleFormattedText(A.normal[A.bold[pods[0].text],
                                        ": {}".format(result)])
            dave.config.redis.setex(key, 60, res)
            bot.reply(source, sender, res)
