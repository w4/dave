# -*- coding: utf-8 -*-
"""Get the average BTC price from preev for bitfinex, bitstamp and btce"""
from __future__ import division

import pickle

import dave.module
import dave.modules
import dave.config
import requests
import babel.numbers
import decimal
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

@dave.module.help("Syntax: btc. Get the current BTC prices from preev.")
@dave.module.command(["btc"], '?([a-zA-Z]*)?')
def btc(bot, args, sender, source):
    crypto(bot, ['btc', args[0]], sender, source)


@dave.module.help("Syntax: ltc. Get the current LTC prices from preev.")
@dave.module.command(["ltc"], '?([a-zA-Z]*)?')
def ltc(bot, args, sender, source):
    crypto(bot, ['ltc', args[0]], sender, source)

@dave.module.help("Syntax: crypto [btc/ltc/etc] (usd/gbp/btc/etc). Get current prices "
                  "from preev. You can also convert cryptocurrency to cryptocurrency.")
@dave.module.command(["crypto", "cryptocurrency"], '([a-zA-Z]*)(?: ([a-zA-Z]*))?')
def crypto(bot, args, sender, source):
    cryptocurrency = args[0].upper()
    cryptoKey = cryptocurrency.lower()

    currency = (args[1] or 'usd').upper()
    currencyKey = currency.lower()

    p = preev(cryptocurrency, currency)

    if p == 'Not found.':
        # Invalid currency.
        bot.reply(source, sender, "Preev doesn't support that currency.")
        return

    if 'usd' in p[cryptoKey] \
            and currencyKey not in p[cryptoKey] and 'usd' in p[currencyKey]:
        # We were given the exchange rate for currency -> usd but not currency -> crypto
        multiplier = 1 / decimal.Decimal(list(p[currencyKey]['usd'].values())[0]['last'])
        currencyKey = 'usd'
    else:
        multiplier = decimal.Decimal(1)

    total_volume = sum(
        float(market['volume']) for market in p[cryptoKey][currencyKey].values()
    )

    avg = sum(
        float(market['last']) * float(market['volume']) / total_volume
            for market in p[cryptoKey][currencyKey].values()
    )

    prices = assembleFormattedText(A.normal[
        A.bold['{} -> {}'.format(cryptocurrency, currency)],
        ': ',
        ', '.join([
            u'{}: {}'.format(
                market,
                babel.numbers.format_currency(decimal.Decimal(data['last']) * multiplier,
                                              currency)
            ) for market, data in p[cryptoKey][currencyKey].items()
        ])
    ])

    prices += u'. average: {}'.format(
        babel.numbers.format_currency(decimal.Decimal(avg) * multiplier,
                                      currency)
    )

    bot.reply(source, sender, prices)

def preev(cryptocurrency, currency):
    """Contact the preev api and get the latest prices and cache for 10 seconds"""
    key = "crypto:{}:{}".format(cryptocurrency, currency)

    if not dave.config.redis.exists(key):
        r = requests.get(
            "http://preev.com/pulse/units:{}+{}/sources:bitfinex+bitstamp+btce".format(
                cryptocurrency,
                currency
            ))

        try:
            json = r.json()
        except:
            return r.text

        dave.config.redis.setex(key, 10, pickle.dumps(json))
    else:
        json = pickle.loads(dave.config.redis.get(key))

    return json
