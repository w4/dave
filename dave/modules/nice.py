# -*- coding: utf-8 -*-
"""Nice."""
import dave.module
import random


@dave.module.help("Nice.", name="nice")
@dave.module.match(r"^nice\.?$")
@dave.module.priority(dave.module.Priority.LOW)
def nice(bot, args, sender, source):
    if random.randint(1, 100) <= 10:
        bot.msg(source, "nice")
