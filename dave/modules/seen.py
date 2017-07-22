import pickle

import dave.module
import dave.config
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
from humanize import naturaltime
from datetime import datetime

@dave.module.help("Syntax: seen [username]. Checks when we last saw a user.")
@dave.module.command(["seen", "lastseen"], r"([A-Za-z_\-\[\]\\^{}|`][A-Za-z0-9_\-\[\]\\^{}|`]*)$")
def seen(bot, args, sender, source):
    if not dave.config.redis.exists("lastseen:{}".format(args[0].lower())):
        bot.reply(source, sender, "I've never seen that user before.")
        return

    seen = pickle.loads(dave.config.redis.get("lastseen:{}".format(args[0].lower())))

    print(seen)

    bot.reply(source, sender, "{} was last seen {} saying: {}".format(
        seen["name"],
        naturaltime(datetime.utcnow() - seen["when"]),
        seen["msg"]
    ))

@dave.module.match(r'(.*)')
@dave.module.always_run()
def log_last_seen(bot, args, sender, source):
    """Whenever someone sends a new message, log what they sent and the time it was sent"""
    dave.config.redis.set("lastseen:{}".format(sender.lower()), pickle.dumps({
        "name": sender,
        "when": datetime.utcnow(),
        "msg": args[0]
    }))