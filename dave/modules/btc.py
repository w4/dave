# -*- coding: utf-8 -*-
"""Get the average BTC price from preev for bitfinex, bitstamp and btce"""
from __future__ import division

import pickle

import dave.module
import dave.modules
import dave.config
import requests
import socket
import babel.numbers
import decimal

@dave.module.help("Syntax: btc. Get the current BTC prices from preev.")
@dave.module.command(["btc"], '?([a-zA-Z]*)?')
@dave.module.priority(dave.module.Priority.HIGHEST)
def btc(bot, args, sender, source):
    currency = (args[0] or 'usd').upper()
    currencyKey = currency.lower()

    p = preev(currency)

    if p == 'Not found.':
        # Invalid currency.
        bot.reply(source, sender, "Preev doesn't support that currency.")
        return

    if 'usd' in p['btc'] and currencyKey not in p['btc'] and 'usd' in p[currencyKey]:
        # We were given the exchange rate for currency -> usd but not currency -> btc
        multiplier = 1 / decimal.Decimal(p[currencyKey]['usd']['other']['last'])
        currencyKey = 'usd'
    else:
        multiplier = decimal.Decimal(1)

    total_volume = sum(
        float(market['volume'])
        for market in p['btc'][currencyKey].itervalues()
    )

    avg = sum(
        float(market['last']) * float(market['volume']) / total_volume
        for market in p['btc'][currencyKey].itervalues()
    )

    prices = ', '.join([
        u'{}: {}'.format(
            market,
            babel.numbers.format_currency(decimal.Decimal(data['last']) * multiplier,
                                          currency)
        ).encode('utf-8')
        for market, data in p['btc'][currencyKey].iteritems()
    ])

    prices += u'. average: {}'.format(
        babel.numbers.format_currency(decimal.Decimal(avg) * multiplier,
                                      currency)
    ).encode('utf-8')

    bot.reply(source, sender, prices.decode('utf-8'))

def preev(currency):
    """Contact the preev api and get the latest prices and cache for 10 seconds"""
    key = "btc:{}".format(currency)

    if not dave.config.redis.exists(key):
        r = requests.get(
            "http://preev.com/pulse/units:btc+{}/sources:bitfinex+bitstamp+btce".format(
                currency
            ))

        json = r.json()

        dave.config.redis.setex(key, 10, pickle.dumps(json))
    else:
        json = pickle.loads(dave.config.redis.get(key))

    return json
