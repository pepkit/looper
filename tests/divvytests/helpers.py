""" Test helpers """

import random
import string


def get_random_key(n=10):
    """
    Randomly generate string key.

    :param int n: Length/size of key to generate
    :return str: Randomize text key
    """
    if not isinstance(n, int):
        raise TypeError("Non-integral key size".format(n))
    if n < 1:
        raise ValueError("Non-positive key size: {}".format(n))
    return "".join(random.choice(string.ascii_letters) for _ in range(n))
