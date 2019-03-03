# -*- coding: utf-8 -*-
"""Reply with donk music whenever anyone mentions donk."""
import dave.module
import random


@dave.module.help("Puts a donk on it.", name="donk")
@dave.module.match(r"(.*)(d(\S+\s)o(\S+\s)n(\S+\s)k|donk)(.*)")
@dave.module.priority(dave.module.Priority.LOW)
def donk(bot, args, sender, source):
    bot.msg(source, "https://www.youtube.com/watch?v={}".format(random.choice(["ckMvj1piK58", "5dQkhKk5Kgk", "qAugqv8e2KM", "ctWh_AEA6RY", "LxXnmkNEyh4", "ckMvj1piK58"])))
