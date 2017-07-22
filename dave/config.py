import redis
import json
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import socket
import markovify
import nltk
import re

# read the config file
basepath = os.path.dirname(__file__)

with open(os.path.abspath(os.path.join(basepath, "..", "config.json")), "r") as config:
    config = json.load(config)

# setup redis caching
redis = redis.StrictRedis(host=config["redis"]["host"], port=config["redis"]["port"],
                          db=config["redis"]["db"])

# connect to the database
db = create_engine(config["database"])
Session = sessionmaker(bind=db)
session = Session()