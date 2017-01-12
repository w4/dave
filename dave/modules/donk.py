# -*- coding: utf-8 -*-
"""Reply with donk music whenever anyone mentions donk."""
import dave.module


@dave.module.help("Puts a donk on it.", name="donk")
@dave.module.match(r"(.*)donk(.*)")
@dave.module.priority(dave.module.Priority.LOW)
def donk(bot, args, sender, source):
    bot.msg(source, "https://www.youtube.com/watch?v=ckMvj1piK58")
