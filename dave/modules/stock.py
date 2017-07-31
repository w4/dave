"""Gets stock information for a given stock."""
import sys

import dave.module
import dave.config
import pickle
from requests import get
from twisted.words.protocols.irc import assembleFormattedText, attributes as A


@dave.module.help("Syntax: stock [symbol].")
@dave.module.ratelimit(1, 1)
@dave.module.command(["stock"], "([a-zA-Z.]+)")
def stock(bot, args, sender, source):
    try:
        resp = yql(args[0])
    except:
        bot.reply(source, sender, "Couldn't get stock data: {}".format(sys.exc_info()[0]))
        raise

    if resp["count"] == 0:
        bot.reply(source, sender, assembleFormattedText(
            A.normal["Couldn't find the ticker symbol ", A.bold[args[0]]]
        ))
        return

    quote = resp["results"]["quote"]

    if quote["LastTradePriceOnly"] is None:
        bot.reply(source, sender, assembleFormattedText(
            A.normal["Couldn't find the ticker symbol ", A.bold[args[0]]]
        ))
        return

    change = float(quote["Change"])
    price = float(quote["LastTradePriceOnly"])
    name = quote["Name"]

    if price == 0 and change == 0:
        # Company is dead
        bot.reply(source, sender, assembleFormattedText(
            A.normal[A.bold[name], " is no longer trading."]
        ))
        return

    color = A.fg.gray

    percent = (change / (price - change)) * 100

    if change > 0:
        color = A.fg.green
        change = "+{}".format(change)
    elif change < 0:
        color = A.fg.lightRed

    bot.reply(source, sender, assembleFormattedText(
        A.normal[
            A.bold[name], " (",  A.bold[quote["Symbol"]], "): ",
            str(price), " ", color["{} ({:.2f}%)".format(change, percent)]
        ]
    ))

def yql(symbol):
    """Get the response from YQL."""
    if not dave.config.redis.exists("stock:{}".format(symbol)):
        request = get("http://query.yahooapis.com/v1/public/yql", params={
            "q": 'SELECT * FROM yahoo.finance.quote WHERE symbol="{}" LIMIT 1'.format(
                symbol
            ),
            "env": "store://datatables.org/alltableswithkeys",
            "format": "json"
        })

        resp = request.json()["query"]
        dave.config.redis.setex("stock:{}".format(symbol), 10, pickle.dumps(resp))
    else:
        resp = pickle.loads(dave.config.redis.get("stock:{}".format(symbol)))

    return resp