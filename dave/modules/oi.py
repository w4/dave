# -*- coding: utf-8 -*-
"""Reply with oi music whenever anyone mentions oi."""
import dave.module


@dave.module.help("Get's oi oi oi in here", name="oi")
@dave.module.match(r"(.*)oi oi oi(.*)")
@dave.module.priority(dave.module.Priority.LOW)
def donk(bot, args, sender, source):
    bot.msg(source, "https://www.youtube.com/watch?v=dTek4AdPkik")
