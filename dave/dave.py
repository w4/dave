# -*- coding: utf-8 -*-
import sys
from datetime import datetime

from humanize import naturaltime
from twisted.internet import reactor, protocol, ssl
from twisted.words.protocols import irc
from twisted.python import log
import time
import pkgutil
import dave.modules as modules
import re
import subprocess
import dave.config as config
import requests
from twisted.internet import reactor, task
from twisted.internet.threads import deferToThread


class Dave(irc.IRCClient):
    nickname = config.config["irc"]["nick"]

    def __init__(self):
        Dave.instance = self

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        log.msg("Connected to server at {} with name {}".format(
                time.asctime(time.localtime(time.time())), self.nickname))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        log.err("Disconnected from server at {}".format(
                time.asctime(time.localtime(time.time()))))

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.mode(self.nickname, True, "B")

        for channel in config.config["irc"]["channels"]:
            self.join(channel)

        if config.config["irc"]["nickserv_password"]:
            self.msg("nickserv", "identify {}".format(config.config["irc"]["nickserv_password"]))

    def joined(self, channel):
        """This will get called when the bot joins the channel."""

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        nick = user.split("!", 1)[0]
        log.msg("<{}> {}".format(nick, msg))

        path = modules.__path__
        prefix = "{}.".format(modules.__name__)

        method = (99999, None)  # priority, method to run
        run = []  # methods which match the message which should be run regardless of priority

        if channel == self.nickname:
            # message was sent directly to the bot to respond directly back to the user
            channel = nick

        for importer, modname, ispkg in pkgutil.iter_modules(path, prefix):
            m = importer.find_module(modname).load_module(modname)

            for name, val in m.__dict__.items():
                if callable(val) and hasattr(val, "rule"):
                    priority = val.priority.value if hasattr(val, "priority") else 0

                    if method[0] < priority and not hasattr(val, "always_run"):
                        continue

                    for rule in val.rule:
                        if channel == nick:
                            # message was sent directly to the bot so make name optional
                            regex = r"^(?:{}(?::|,|) )?(.*)$".format(self.nickname) \
                                if rule["named"] else r"^(.*)$"
                        else:
                            regex = r"^{}(?::|,|) (.*)$".format(self.nickname) \
                                if rule["named"] else r"^(.*)$"

                        match = re.match(regex, msg)

                        if match:
                            match = re.match(rule["pattern"], match.group(1))

                            if match:
                                if hasattr(val, "always_run"):
                                    run.append((val, match.groups()))
                                else:
                                    method = (priority, val, match.groups())

        if method[1] is not None:
            # we matched a command
            deferToThread(method[1], self, method[2], nick, channel)

            if not (hasattr(method[1], "dont_always_run") and method[1].dont_always_run):
                # if dont_always_run is set, the command the user sent doesn't
                # want "always run" modules to run.
                for m in run:
                    # modules that should always be run regardless of priority
                    deferToThread(m[0], self, m[1], nick, channel)

    def irc_unknown(self, prefix, command, params):
        if command == "INVITE":
            self.join(params[1])

    def msg(self, user, message, length=None):
        """Override msg() to log what the bot says"""
        log.msg("<{}> {}".format(self.nickname, message))
        super(Dave, self).msg(user, message, length)

    def reply(self, source, sender, msg):
        if source == sender:
            # responding directly back to the user so don't tag them
            self.msg(source, msg)
        else:
            self.msg(source, "{}: {}".format(sender, msg))

def autopull():
    log.msg("Pulling latest code from git.")
    output = subprocess.check_output(["git", "pull"])

    if not "Already up-to-date" in str(output):
        # check latest commit message
        args = ["git", "log", "-1", "--pretty=format:{}".format(",".join([
            "%h", "%s", "%at", "%an", "%ae"
        ]))]
        output = subprocess.check_output(args).split(b",")
        log.msg("Pulled latest commit.")

        # get a shortened git commit url
        try:
            r = requests.post('https://git.io/', {
                "url": "https://github.com/{}/commit/{}".format(
                    config.config["repo"],
                    str(output[0], 'utf-8')
                )
            }, allow_redirects=False, timeout=3)

            commit = r.headers['Location']
        except:
            commit = ""

        msg = "{} ({}) authored by {} ({}) {} {}".format(
            str(output[1], 'utf-8'),
            str(output[0], 'utf-8'),
            str(output[3], 'utf-8'),
            str(output[4], 'utf-8'),
            naturaltime(datetime.utcnow().timestamp() -
                        float(output[2])),
            commit
        )

        log.msg("Updated, {}".format(msg))

        if hasattr(Dave, "instance"):
            for channel in config.config["irc"]["channels"]:
                Dave.instance.msg(channel, msg)
    else:
        log.msg("Already up to date.")

def main():
    log.startLogging(sys.stdout)

    # pull from github every 2 minutes
    task.LoopingCall(lambda: deferToThread(autopull)).start(120.0)

    factory = protocol.ReconnectingClientFactory.forProtocol(Dave)
    reactor.connectSSL(config.config["irc"]["host"], config.config["irc"]["port"],
                       factory, ssl.ClientContextFactory())
    reactor.run()
