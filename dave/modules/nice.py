# -*- coding: utf-8 -*-
"""Nice."""
import dave.module


@dave.module.help("Nice.", name="nice")
@dave.module.match(r"^nice\.?$")
@dave.module.priority(dave.module.Priority.LOW)
def donk(bot, args, sender, source):
    bot.msg(source, "nice")
