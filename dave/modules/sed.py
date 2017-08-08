# -*- coding: utf-8 -*-
"""Pass any messages beginning with 'sed' to GNU sed."""
import dave.module
import dave.config
import re
from twisted.python import log

@dave.module.help("Syntax: s/find/replace/flags", "sed")
@dave.module.match(r"^((s|y)(/|\||!)(.*?)(\3)(.*?)(\3)([gIi]+)?)$")
@dave.module.priority(dave.module.Priority.HIGHEST)
def sed(bot, args, sender, source):
    key = "msg:{}:{}".format(source, sender)

    for i, msg in enumerate(dave.config.redis.lrange(key, 0, -1)):
        try:
            msg = msg.decode('utf-8')
        except Exception as e:
            log.err(e, "Failed decoding previous messages from redis.")
            continue

        flags = list(args[7]) if args[7] else []
        f = re.UNICODE

        if 'I' in flags or 'i' in flags:
            f = f | re.IGNORECASE

        try:
            # bold replacements
            toDisplay = re.sub(args[3], "\x02{}\x0F".format(args[5]) if args[5] else "",
                               msg, count=0 if 'g' in flags else 1, flags=f)
            toSave = re.sub(args[3], args[5], msg,
                            count=0 if 'g' in flags else 1, flags=f)
        except Exception as e:
            bot.reply(source, sender,
                      "There was a problem with your sed command: {}".format(str(e)))
            return

        if toSave != msg:
            bot.msg(source, "<{}> {}".format(sender, toDisplay.strip()))
            dave.config.redis.lset(key, i, toSave.strip())
            return


@dave.module.match(r"(.*)")
@dave.module.priority(dave.module.Priority.LOWEST)
def update_cache(bot, args, sender, source):
    key = "msg:{}:{}".format(source, sender)
    dave.config.redis.lpush(key, args[0])
    dave.config.redis.ltrim(key, 0, 2)
