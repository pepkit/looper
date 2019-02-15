""" Definitions of the parser argument types """

import attmap
from peppy import FLAGS

# Templates

def checkbox_f(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "checkbox",
                "element_args": {
                    # "checked": "False"
                }})
    return caravel_data if caravel else eval(x)


def checkbox_t(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "checkbox",
                "element_args": {
                    "checked": "True"
                }})
    return caravel_data if caravel else eval(x)


def range_010(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "range",
                "element_args": {
                    "min": "0",
                    "max": "10"
                }})
    return caravel_data if caravel else int(x)


# Definitions

file_checks = checkbox_t
allow_duplicate_names = all_folders = force_yes = dry_run = ignore_flags = checkbox_f
lumpn = limit = range_010


def flags(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "select",
                "element_args": {
                    "option": FLAGS
                }})
    return caravel_data if caravel else x


def time_delay(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "range",
                "element_args": {
                    "min": "0",
                    "max": "30",
                    "value": "0"
                }})
    return caravel_data if caravel else int(x)


def lump(x, caravel=False):
    caravel_data = attmap.AttMap({
                "element_type": "range",
                "element_args": {
                    "min": "0",
                    "max": "100",
                    "value": "100",
                    "step": "0.1"
                }})
    return caravel_data if caravel else float(x)
