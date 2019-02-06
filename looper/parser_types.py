""" Definitions of the parser argument types """

import attmap
from peppy import FLAGS


def flags(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "select",
                "element_args": {
                    "option": FLAGS
                }})
    return caravel_data if caravel else x


def limit(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "range",
                "element_args": {
                    "min": "0",
                    "max": "10"
                }})
    return caravel_data if caravel else int(x)
