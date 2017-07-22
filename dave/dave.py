# -*- coding: utf-8 -*-
import sys
from twisted.internet import reactor, protocol, ssl
from twisted.words.protocols import irc
from twisted.python import log
import time
import pkgutil
import modules
import re
import config
import datetime
from twisted.internet.threads import deferToThread


class Dave(irc.IRCClient):
    nickname = bytes(config.config["irc"]["nick"])

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
            self.join(bytes(channel))

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

        for importer, modname, ispkg in pkgutil.iter_modules(path, prefix):
            m = importer.find_module(modname).load_module(modname)

            for name, val in m.__dict__.iteritems():
                if callable(val) and hasattr(val, "rule"):
                    priority = val.priority.value if hasattr(val, "priority") else 0

                    if method[0] < priority and not hasattr(val, "always_run"):
                        continue

                    for rule in val.rule:
                        regex = r"^{}(?::|,|) (.*)$".format(self.nickname) if rule["named"] else r"^(.*)$"

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
            method[1](self, method[2], nick, channel)

        for m in run:
            # modules that should always be run regardless of priority
            m[0](self, m[1], nick, channel)

    def irc_unknown(self, prefix, command, params):
        if command == "INVITE":
            self.join(params[1])

    def reply(self, source, sender, msg):
        self.msg(source, "{}: {}".format(sender, msg.encode("utf-8")))


def main():
    log.startLogging(sys.stdout)

    factory = protocol.ReconnectingClientFactory()
    factory.protocol = Dave
    reactor.connectSSL(config.config["irc"]["host"], config.config["irc"]["port"],
                       factory, ssl.ClientContextFactory())
    reactor.run()
