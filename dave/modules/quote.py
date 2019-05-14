"""Quote system"""
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func
import dave.module
import dave.config
import uuid
import random
import os
from dave.models import Quote
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

random.seed(os.urandom(64))

@dave.module.help("Syntax: aq [quote]. Add a quote.")
@dave.module.command(["aq", "addquote"], "(.*)$")
@dave.module.ratelimit(1, 2)
def add_quote(bot, args, sender, source):
    generated_uuid = str(uuid.uuid4())
    quote = Quote(id=generated_uuid, quote=args[0], attributed=None, added_by=sender)
    dave.config.session.add(quote)

    bot.reply(source, sender, assembleFormattedText(
        A.normal["Successfully added quote: ", A.bold[args[0]]]))

    bot.msg(sender, "You can remove this quote later using \"dave dq {}\"".format(
        generated_uuid))

@dave.module.help("Syntax: q. Return a random quote.")
@dave.module.command(["q", "quote"])
@dave.module.ratelimit(1, 1)
def quote(bot, args, sender, source):
    query = dave.config.session.query(Quote)

    if not query.count():
        bot.reply(source, sender, "No quotes found.")
        return

    row = query.order_by(func.random()).first()

    bot.reply(source, sender, assembleFormattedText(A.normal[
        "<{}> ".format(row.attributed.strip()) if row.attributed else "", A.bold[row.quote]
    ]))

@dave.module.help("Syntax: fq [search]. Search for a quote.")
@dave.module.command(["fq", "findquote"], "(.*)$")
@dave.module.ratelimit(1, 3)
def find_quote(bot, args, sender, source):
    try:
        quotes = dave.config.session.query(Quote).filter(
            (Quote.quote.op("~")(args[0])) | (Quote.attributed.op("~")(args[0]))
                | (Quote.added_by.op("~")(args[0]))
        ).all()
    except SQLAlchemyError as e:
        bot.reply(source, sender, SQLAlchemyError.__str__(e))
        return

    if len(quotes) == 0:
        bot.reply(source, sender, "No results for query.")

    if len(quotes) > 3:
        bot.reply(source, sender, "Your query returned too many results ({}), here's a " \
                                  "random sample:".format(len(quotes)))
        quotes = random.sample(quotes, 3)

    for quote in quotes:
        bot.reply(source, sender, assembleFormattedText(A.normal[
            "<{}> ".format(quote.attributed.strip()) if quote.attributed else "", A.bold[quote.quote]
        ]))

@dave.module.help("Syntax: dq [uuid]. Allow the quote owner to delete a quote.")
@dave.module.command(["dq", "deletequote"], "(.*)$")
@dave.module.ratelimit(1, 1)
def delete_quote(bot, args, sender, source):
    query = dave.config.session.query(Quote).filter(Quote.id == args[0])

    if not query.count():
        bot.reply(source, sender, "Couldn't find a quote with that UUID.")
        return

    query.delete()
    bot.reply(source, sender, "Successfully deleted quote.")
