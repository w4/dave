# -*- coding: utf-8 -*-
"""Chatter bot using Markov chains."""
import dave.module
import dave.config
import random
import re
from dave.models import Message

FACTOR = 0.05


@dave.module.help("Syntax: babble [optional seeds].")
@dave.module.command(["babble"], "?(.*)")
@dave.module.priority(dave.module.Priority.HIGHEST)
def babble(bot, args, sender, source):
    msg = args[0].strip()

    if msg:
        args = msg.split(" ")

        if len(args) == 2:
            # require two seeds
            resp = dave.config.markov.make_sentence(tuple(dave.config.markov.word_split(" ".join(args))), tries=10000)
        else:
            resp = None
    else:
        resp = dave.config.markov.make_sentence(tries=10000)

    if not resp is None:
        bot.msg(source, resp.encode("utf-8"))


#@dave.module.match(r"(.*)")
#@dave.module.always_run()
#def random_babble(bot, args, sender, source):
#    if not args[0].startswith(bot.nickname) and random.random() < FACTOR:
#        # every (factor*100)% of messages should be babbled about
#        babble(bot, args, sender, source)
