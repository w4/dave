import redis
import json
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import socket
import socks
import markovify
import nltk
from models import Message
import re

# read the config file
basepath = os.path.dirname(__file__)

with open(os.path.abspath(os.path.join(basepath, "..", "config.json")), "r") as config:
    config = json.load(config)

# setup redis caching
redis = redis.StrictRedis(host=config["redis"]["host"], port=config["redis"]["port"],
                          db=config["redis"]["db"])

# set everything to use our socks proxy
proxy = config['socks'].split(":")

default_socket = socket.socket

if proxy[0]:
    socks.set_default_proxy(socks.SOCKS5, proxy[0], int(proxy[1]))
    proxied_socket = socks.socksocket
else:
    proxied_socket = socket.socket

# connect to the database
db = create_engine(config["database"])
Session = sessionmaker(bind=db)
session = Session()

# setup the markov chain
class PText(markovify.NewlineText):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

if not redis.exists("markov:chain"):
    markov = PText("\n".join([m[0] for m in session.query(Message.message).all()]), state_size=2)
    redis.setex("markov:chain", 500, markov.chain.to_json())
else:
    markov = PText("\n".join([m[0] for m in session.query(Message.message).all()]),
                   state_size=2, chain=markovify.Chain.from_json(redis.get("markov:chain")))
