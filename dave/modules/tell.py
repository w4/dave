"""Tell a user something next time we see them."""
import dave.module
import dave.config
import pickle


@dave.module.help("Syntax: tell [user] [message]. Tell a user something when we next "
                  "see them")
@dave.module.command(["tell"], "([A-Za-z_\-\[\]\\^{}|`][A-Za-z0-9_\-\[\]\\^{}|`]*) (.*)")
@dave.module.ratelimit(1, 3)
def tell(bot, args, sender, source):
    dave.config.redis.lpush("tell:{}".format(args[0].lower()), pickle.dumps({
        "sender": sender,
        "msg": args[1]
    }))
    bot.reply(source, sender, "I'll let {} know when they're back.".format(args[0]))


@dave.module.match(r"(.*)")
@dave.module.always_run()
def check_msgs(bot, args, sender, source):
    msgs = dave.config.redis.lrange("tell:{}".format(sender.lower()), 0, -1)

    if msgs and len(msgs):
        bot.msg(sender, "You have messages waiting for you:")

        for msg in msgs:
            msg = pickle.loads(msg)
            bot.msg(sender, "<{}> {}".format(msg["sender"], msg["msg"]))

        dave.config.redis.delete("tell:{}".format(sender.lower()))