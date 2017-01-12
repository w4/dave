# -*- coding: utf-8 -*-
"""Pass any messages beginning with 'sed' to GNU sed."""
import subprocess
import dave.module
import dave.config
import re


@dave.module.help("Syntax: s/find/replace/flags", "sed")
@dave.module.match(r"^((s|y)(/|\||!)(.*?)(\3)(.*?)(\3)([gIi]+)?)$")
@dave.module.priority(dave.module.Priority.HIGHEST)
def sed(bot, args, sender, source):
    key = "msg:{}:{}".format(source, sender)

    for i, msg in enumerate(dave.config.redis.lrange(key, 0, -1)):
        flags = list(args[7]) if args[7] else []
        f = re.UNICODE

        if 'I' in flags or 'i' in flags:
            f = f | re.IGNORECASE

        try:
            replace = re.sub(args[3], args[5], msg, count=0 if 'g' in flags else 1,
                             flags=f)
            print(replace)
        except Exception as e:
            bot.reply(source, sender,
                      "There was a problem with your sed command: {}".format(str(e)))
            return

        if replace.strip() != msg:
            msg = replace.strip()
            bot.msg(source, "{} meant: {}".format(sender, msg))
            dave.config.redis.lset(key, i, msg)
            return


@dave.module.match(r"^(?!(?:s|y)([\x00-\x7F])(?:.*?)(?:\1)(?:.*?)(?:\1)(?:[gIi\d]+)?)(.*)$")
@dave.module.priority(dave.module.Priority.LOWEST)
def update_cache(bot, args, sender, source):
    key = "msg:{}:{}".format(source, sender)
    dave.config.redis.lpush(key, args[1])
    dave.config.redis.ltrim(key, 0, 2)
