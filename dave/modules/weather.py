# -*- coding: utf-8 -*-
"""Get the weather from an address using forecast.io."""
from __future__ import division
import dave.modules
import requests
import dave.config
import pickle
from urllib.parse import quote_plus
import arrow
from dave.models import Location
import socket


@dave.module.help("Syntax: weather [location]. Get the forecast in the specified location.")
@dave.module.command(["weather"], "?( .*)?$")
@dave.module.priority(dave.module.Priority.HIGHEST)
@dave.module.ratelimit(1, 5)
def weather(bot, args, sender, source):
    location = args[0]

    db_location = dave.config.session.query(Location).filter(Location.nick.ilike(sender)).first()

    if not location:
        if db_location:
            location = db_location.location
        else:
            return
    else:
        location = location.strip()

        if db_location:
            db_location.location = location
        else:
            db_location = Location(nick=sender, location=location)
            dave.config.session.add(db_location)

    geocode = get_location(location)

    if not geocode or not geocode["results"]:
        return

    formatted_address = get_address(geocode)
    timezone = get_timezone(geocode)
    weather = get_weather(geocode)

    bot.reply(source, sender, u"{}: {}°C/{}°F (feels like {}°C/{}°F), {}. Wind: {}mph/{}km/h, humidity: {}% | Sun: {} - {} {}".format(
        formatted_address,
        int(round(weather["currently"]["temperature"])),
        int(round(weather["currently"]["temperature"] * (9 / 5) + 32)),
        int(round(weather["currently"]["apparentTemperature"])),
        int(round(weather["currently"]["apparentTemperature"] * (9 / 5) + 32)),
        weather["currently"]["summary"],
        int(round(weather["currently"]["windSpeed"])),
        int(round(weather["currently"]["windSpeed"] * 1.60934)),
        int(round(weather["currently"]["humidity"] * 100)),
        arrow.get(weather["daily"]["data"][0]["sunriseTime"]).to(timezone["zoneName"] or "UTC").strftime("%H:%M").lower(),
        arrow.get(weather["daily"]["data"][0]["sunsetTime"]).to(timezone["zoneName"] or "UTC").strftime("%H:%M").lower(),
        timezone["abbreviation"] or "UTC"
    ))


def get_location(location):
    """Get the lat/long of the location the user gave us."""
    key = "location:{}".format(location.lower())

    if not dave.config.redis.exists(key):
        r = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(
            quote_plus(location),
            dave.config.config["api_keys"]["google_maps"]
        ))

        geocode = r.json()

        dave.config.redis.set(key, pickle.dumps(geocode))
    else:
        geocode = pickle.loads(dave.config.redis.get(key))

    return geocode


def get_address(geocode):
    """Get a nicely formatted location to return."""
    formatted_address = []

    has_locality = False

    for component in geocode["results"][0]["address_components"]:
        if "locality" in component["types"]:
            has_locality = True
            formatted_address.append(component["short_name"])

        if "country" in component["types"]:
            formatted_address.append(component["short_name"])

    if not has_locality:
        for component in geocode["results"][0]["address_components"]:
            if "postal_town" in component["types"]:
                formatted_address.insert(0, component["short_name"])

    if len(formatted_address) < 2:
        formatted_address = [a["short_name"] for a in geocode["results"][0]["address_components"]]

    return ", ".join(formatted_address)


def get_timezone(geocode):
    """Get the timezone of the location the user gave us"""
    key = "timezone:{}_{}".format(geocode["results"][0]["geometry"]["location"]["lat"],
                                  geocode["results"][0]["geometry"]["location"]["lng"])

    if not dave.config.redis.exists(key):
        r = requests.get("http://api.timezonedb.com/?key={}&lat={}&lng={}&format=json".format(
            dave.config.config["api_keys"]["timezonedb"],
            geocode["results"][0]["geometry"]["location"]["lat"],
            geocode["results"][0]["geometry"]["location"]["lng"]
        ))

        timezone = r.json()

        dave.config.redis.set(key, pickle.dumps(timezone))
    else:
        timezone = pickle.loads(dave.config.redis.get(key))

    return timezone


def get_weather(geocode):
    """Get the weather for the location the user gave us"""
    key = "weather:{}_{}".format(geocode["results"][0]["geometry"]["location"]["lat"],
                                 geocode["results"][0]["geometry"]["location"]["lng"])

    if not dave.config.redis.exists(key):
        r = requests.get("https://api.forecast.io/forecast/{}/{},{}?units=uk2".format(
            dave.config.config["api_keys"]["forecast.io"],
            geocode["results"][0]["geometry"]["location"]["lat"],
            geocode["results"][0]["geometry"]["location"]["lng"]
        ))

        json = r.json()

        dave.config.redis.setex(key, 300, pickle.dumps(json))
    else:
        json = pickle.loads(dave.config.redis.get(key))

    return json
