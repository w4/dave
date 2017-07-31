from dave.config import redis

def ratelimit(fun, userhost):
    """
    Ratelimit a function

    :param fun: Function to ratelimit
    :param userhost: Host of the user
    :return: True, if this function is allowed to be executed
    """
    if not hasattr(fun, "ratelimit"):
        return True

    # how many requests are allowed per "per" seconds
    value = fun.ratelimit["value"]
    # how long before the ratelimit is reset
    per = fun.ratelimit["per"]

    key = "ratelimit:{}:{}:{}".format(userhost, fun.__module__, fun.__qualname__)

    if not redis.exists(key):
        # ratelimit doesn't exist, make a new one
        redis.setex(key, per, 0)
    elif int(redis.get(key)) >= value:
        # ratelimit has been exceed
        return False

    redis.incr(key)
    return True

