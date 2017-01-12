# -*- coding: utf-8 -*-
"""Give the user a link to our repo."""
import dave.module
import dave.config


@dave.module.help("Get the GitHub repository that hosts the code for this bot.")
@dave.module.command(["repo"])
@dave.module.priority(dave.module.Priority.HIGHEST)
def repo(bot, args, sender, source):
    bot.reply(source, sender, "https://github.com/{}".format(dave.config.config['repo']))
