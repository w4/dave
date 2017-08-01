"""Return some useful reddit info"""
import pickle
from datetime import datetime
import dave.module
import dave.config
from twisted.words.protocols.irc import assembleFormattedText, attributes as A
from requests import get
from humanize import naturaltime, naturaldelta, intcomma

@dave.module.match(r'.*(?:^| )(?:https?://(?:www\.)?reddit.com)?(/r/(.+)/comments/([^\s]+))(?: |$).*')
@dave.module.match(r'.*(?:^| )https?://(?:www\.)?redd.it/([^\s]+)(?: |$).*')
@dave.module.ratelimit(1, 1)
@dave.module.dont_always_run_if_run()
def post(bot, args, sender, source):
    """Ran whenever a reddit post is sent"""
    if dave.config.redis.exists("reddit:post:mentioned:{}:{}".format(args[0], source)):
        # if this post was mentioned in the last x seconds (see the setex below),
        # don't spam info about it
        return

    if not dave.config.redis.exists("reddit:post:{}".format(args[0])):
        req = get("https://reddit.com/{}.json?limit=1".format(args[0]),
                  headers={'user-agent': 'irc bot (https://github.com/w4)'})

        if req.status_code != 200:
            return

        req = req.json()

        dave.config.redis.setex("reddit:post:{}".format(args[0]), 200,
                                pickle.dumps(req))
    else:
        req = pickle.loads(dave.config.redis.get("reddit:post:{}".format(args[0])))

    resp = req[0]["data"]["children"][0]["data"]

    dave.config.redis.setex("reddit:post:mentioned:{}:{}".format(args[0], source), 300, 1)

    bot.msg(source, assembleFormattedText(
        A.normal[
            A.bold[A.fg.lightRed["[NSFW] "]] if resp["over_18"] else "",
            A.bold[resp["title"][:75] + (resp["title"][75:] and '...')],
            " by ", A.bold[resp["author"]],
            " (/r/{}) {} comments, {} points, posted {}".format(
                resp["subreddit"],
                intcomma(resp["num_comments"]),
                intcomma(resp["score"]),
                naturaltime(datetime.utcnow().timestamp() - resp["created_utc"])
            ),
        ]
    ))

@dave.module.match(r'.*(?:^| )(?:https?://(?:www\.)?reddit.com)?/r/(([^\s/]+))/?(?: |$).*')
@dave.module.ratelimit(1, 1)
@dave.module.dont_always_run_if_run()
def subreddit(bot, args, sender, source):
    """Ran whenever a subreddit is mentioned"""
    if dave.config.redis.exists("reddit:subreddit:mentioned:{}:{}".format(args[0], source)):
        # if this subreddit was mentioned in the last x seconds (see the setex below),
        # don't spam info about it
        return

    if not dave.config.redis.exists("reddit:subreddit:{}".format(args[0])):
        req = get("https://reddit.com/r/{}/about.json".format(args[0]),
                  headers={'user-agent': 'irc bot (https://github.com/w4)'})

        if req.status_code != 200:
            return

        if "/search.json" in req.url:
            # 404'd, reddit redirected us to the search page because they couldn't find
            # the user.
            return

        req = req.json()

        dave.config.redis.setex("reddit:subreddit:{}".format(args[0]), 600,
                                pickle.dumps(req))
    else:
        req = pickle.loads(dave.config.redis.get("reddit:subreddit:{}".format(args[0])))

    resp = req["data"]

    # don't give info about this user again in this channel for 300 seconds
    dave.config.redis.setex("reddit:subreddit:mentioned:{}:{}".format(args[0], source),
                            300, 1)

    bot.msg(source, assembleFormattedText(
        A.normal[
            A.bold[A.fg.lightRed["[NSFW] "]] if resp["over18"] else "",
            A.bold[resp["title"]],
            " ({}), a community for {}. {} subscribers, {} browsing right now.".format(
                resp["display_name_prefixed"],
                naturaldelta(datetime.utcnow().timestamp() - resp["created"]),
                intcomma(resp["subscribers"]),
                intcomma(resp["accounts_active"])
            )
        ]
    ))


@dave.module.match(r'.*(?:^| )(?:https?://(?:www\.)?reddit.com)?/(?:u|user)/(([^\s]+)/?)(?: |$).*')
@dave.module.ratelimit(1, 1)
@dave.module.dont_always_run_if_run()
def user(bot, args, sender, source):
    if dave.config.redis.exists("reddit:user:mentioned:{}:{}".format(args[0], source)):
        # if this user was mentioned in the last x seconds (see the setex below), don't
        # spam info about them
        return

    if not dave.config.redis.exists("reddit:user:{}".format(args[0])):
        req = get("https://reddit.com/u/{}/about.json".format(args[0]),
                  headers={'user-agent': 'irc bot (https://github.com/w4)'})

        if req.status_code != 200:
            return

        req = req.json()

        dave.config.redis.setex("reddit:user:{}".format(args[0]), 600,
                                pickle.dumps(req))
    else:
        req = pickle.loads(dave.config.redis.get("reddit:user:{}".format(args[0])))

    resp = req["data"]

    # don't give info about this user again in this channel for 300 seconds
    dave.config.redis.setex("reddit:user:mentioned:{}:{}".format(args[0], source), 300, 1)

    bot.msg(source, assembleFormattedText(
        A.normal[
            A.bold[resp["name"]],
            ", a redditor for {}. {} link karma, {} comment karma.".format(
                naturaldelta(datetime.utcnow().timestamp() - resp["created"]),
                intcomma(resp["link_karma"]),
                intcomma(resp["comment_karma"])
            ),
            " Verified user." if resp["verified"] else "",
            " Reddit employee." if resp["is_employee"] else ""
        ]
    ))
