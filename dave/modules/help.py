# -*- coding: utf-8 -*-
"""Give the user some help regarding modules of Dave."""
import dave.module
import dave.modules
import pkgutil


@dave.module.command(["help"])
def list_modules(bot, args, sender, source):
    """List all the modules the user can get help with."""
    reply = []

    path = dave.modules.__path__
    prefix = "{}.".format(dave.modules.__name__)

    for importer, modname, ispkg in pkgutil.iter_modules(path, prefix):
        m = importer.find_module(modname).load_module(modname)

        for name, val in m.__dict__.items():
            if callable(val) and hasattr(val, "help"):
                reply.append(val.help["name"])

    bot.reply(source, sender, "Modules: {}".format(" ".join(set(reply))))


@dave.module.help("Syntax: help [command]. Get some information about a module.")
@dave.module.command(["help"], "(.*)$")
@dave.module.priority(dave.module.Priority.HIGHEST)
def help(bot, args, sender, source):
    """Give the user help with a single module."""
    path = dave.modules.__path__
    prefix = "{}.".format(dave.modules.__name__)

    for importer, modname, ispkg in pkgutil.iter_modules(path, prefix):
        m = importer.find_module(modname).load_module(modname)

        for name, val in m.__dict__.items():
            if callable(val) and hasattr(val, "rule") and hasattr(val, "help"):
                for rule in val.rule:
                    if "commands" in rule and args[0] in rule["commands"]:
                        bot.reply(source, sender, val.help["message"])
                        return

                if val.help["name"] == args[0]:
                    bot.reply(source, sender, val.help["message"])
