# -*- coding: utf-8 -*-
"""Provide various decorators for dave modules."""
import re
from enum import Enum
import socket
import config


def match(value):
    """Decorate a function to be called whenever a message matches the given pattern.

    Args:
        value: Pattern to match.
    """
    def add_attribute(function):
        if not hasattr(function, "rule"):
            function.rule = []

        function.rule.append({
            "named": False,
            "pattern": re.compile(value)
        })
        return function

    return add_attribute


def command(commands, parameters="?$"):
    """Decorate a function to trigger on lines starting with "$nickname: command"

    Args:
        command: An array of strings which trigger this module.
        parameters: A regular expression rule to capture parameters."""
    def add_attribute(function):
        if not hasattr(function, "rule"):
            function.rule = []
        function.rule.append({
            "named": True,
            "pattern": re.compile("^(?:{}) {}".format("|".join(commands), parameters)),
            "commands": commands
        })
        return function

    return add_attribute


def help(message, name=None):
    """Decorate a function to add a help string."""
    def add_attribute(function):
        if name is None:
            for rule in function.rule:
                if "commands" in rule:
                    n = rule["commands"][0]
        else:
            n = name

        if not hasattr(function, "priority"):
            function.priority = Priority.NORMAL

        function.help = {
            "message": message,
            "name": n
        }
        return function

    return add_attribute


def priority(priority):
    """Decorate a function to add a priority."""
    def add_attribute(function):
        function.priority = priority
        return function

    return add_attribute


def dont_always_run_if_run():
    """If this function is run, we shouldn't run the functions that should always run"""
    def add_attribute(function):
        function.dont_always_run = True
        return function

    return add_attribute


def always_run():
    """Decorate a function to always run it, even when over prioritised"""
    def add_attribute(function):
        function.always_run = True
        return function

    return add_attribute


class Priority(Enum):
    HIGHEST = -2
    HIGH = -1
    NORMAL = 0
    LOW = 1
    LOWEST = 2
