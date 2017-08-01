# -*- coding: utf-8 -*-
import sys
from datetime import datetime

from humanize import naturaltime
from twisted.internet import reactor, protocol, ssl, task
from twisted.words.protocols import irc
from twisted.internet.threads import deferToThread
from twisted.python import log
import time
import pkgutil
import dave.modules as modules
import re
import subprocess
import dave.config as config
import requests
from dave.ratelimit import ratelimit


class Dave(irc.IRCClient):
    nickname = config.config["irc"]["nick"]

    def __init__(self):
        Dave.instance = self

    def lineReceived(self, line):
        """Override lineReceived to ignore invalid characters so non-utf8 messages
        don't crash the bot"""
        if isinstance(line, bytes):
            # decode bytes from transport to unicode
            line = line.decode("utf-8", errors="ignore")

        super(Dave, self).lineReceived(line)

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
        # let everyone know i'm a bot by setting +B on myself
        self.mode(self.nickname, True, "B")

        for channel in config.config["irc"]["channels"]:
            self.join(channel)

        if config.config["irc"]["nickserv_password"]:
            self.msg("nickserv", "identify {}".format(config.config["irc"]["nickserv_password"]))

    def joined(self, channel):
        """This will get called when the bot joins the channel."""

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        nick, userhost = user.split("!", 1)

        log.msg("<{}> {}".format(user, msg))

        # get the absolute path to our modules directory
        path = modules.__path__

        # prefix for names iter_modules outputs so we can import it easily
        prefix = "{}.".format(modules.__name__)

        method = (99999, None)  # priority, command to run
        run = []  # methods which match the message which should be run regardless of priority

        if channel == self.nickname:
            # message was sent directly to the bot to respond directly back to the user
            channel = nick

        # match messages in the format of "username: command"
        match = re.match(r"^(?:{}[:,]? ){}(.*)$".format(
            self.nickname,
            # make the bot name optional if the command was sent via pm to the bot
            "?" if channel == nick else ""
        ), msg)

        # true if this message invokes the bot directly
        invoked = bool(match)

        # use the parsed message if the bot was invoked directly or just use the raw msg
        msg = match.group(1) if invoked else msg

        # loop over all of our modules
        for importer, modname, ispkg in pkgutil.iter_modules(path, prefix):
            # import the module - we should probably optimise this as at the moment
            # every module is loaded every time a message is sent
            m = importer.find_module(modname).load_module(modname)

            # loop over the attributes of this module
            for name, val in m.__dict__.items():
                if not callable(val) or not hasattr(val, "rule"):
                    # only loop over functions that have been decorated by command/match
                    continue

                # get the priority of this method or default to 0. priorities are
                # lower = higher priority
                priority = val.priority.value if hasattr(val, "priority") else 0

                if method[0] < priority and not hasattr(val, "always_run"):
                    # we already know about a command with higher priority. skip this one.
                    continue

                # commands can match multiple commands or rules, loop over each one
                # and see if it matches
                for rule in val.rule:
                    if rule["named"] and not invoked:
                        # this rule wanted to be invoked by name but this message
                        # doesn't invoke the bot directly so lets ignore this message.
                        continue

                    match = re.match(rule["pattern"], msg)

                    if match:
                        # if this method should always run regardless of priority, add it
                        # to the list of things to execute later. if not, update our
                        # method tuple with our newest high priority command.
                        if hasattr(val, "always_run"):
                            run.append((val, match.groups()))
                        else:
                            method = (priority, val, match.groups(), rule["named"])

                        # we've matched a rule for this command already, no need to
                        # keep going.
                        break

        # if this is true then if the dont_always_run flag is set on our command we're
        # about to execute, ignore it and run anyway. currently, this is only used when
        # the user is ratelimited for the command they tried to execute
        ignore_dont_always_run = False

        if method[1] is not None:
            # we matched a command
            if ratelimit(method[1], userhost):
                # not ratelimited, we can run our function!
                deferToThread(method[1], self, method[2], nick, channel)
            elif method[3]:
                # if this was a direct command to the bot, tell them they've been r/l'd
                self.reply(channel, nick, "You have been ratelimited for this command.")
            else:
                # if it wasn't, let the always_run functions run. since it wasn't a direct
                # invoke, we don't need to alert the user about being r/l'd
                ignore_dont_always_run = True

        # we always want this method to run if a command wasn't matched, if the user was
        # ratelimited or if command doesn't have the dont_always_run flag set.
        if method[1] is None or ignore_dont_always_run or \
                not (hasattr(method[1], "dont_always_run") and method[1].dont_always_run):
            # loop over every always_run method that we matched and execute it
            for m in run:
                if not hasattr(m[0], "ratelimit") or ratelimit(m[0], userhost):
                    # modules that should always be run regardless of priority
                    deferToThread(m[0], self, m[1], nick, channel)

    def irc_unknown(self, prefix, command, params):
        if command == "INVITE":
            # join any channels we are invited to
            self.join(params[1])

    def msg(self, dest, message, length=None):
        """Override msg() to log what the bot says and to make msg thread safe."""
        log.msg("<{}> {}".format(self.nickname, message))
        reactor.callFromThread(super(Dave, self).msg, dest, message, length)

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
        args = ["git", "log", "-1", "--pretty=format:{}".format("|||".join([
            "%h", "%s", "%at", "%an", "%ae"
        ]))]
        output = subprocess.check_output(args).split(b"|||")
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
