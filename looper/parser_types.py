""" Definitions of the parser argument types """

import attmap

# Templates


def range(x, caravel=False, min=0, max=10, step=1, value=0):
    caravel_data = attmap.AttMap({
                "element_type": "range",
                "element_args": {
                    "min": str(min),
                    "max": str(max),
                    "step": str(step),
                    "value": str(value)
                }})
    if step < 1:
        return caravel_data if caravel else float(x)
    else:
        return caravel_data if caravel else int(x)


def checkbox(x, caravel=False, checked=False):
    caravel_data = attmap.AttMap({
                "element_type": "checkbox",
                "element_args": {
                }})
    if checked:
        caravel_data.add_entries({"element_args": {'checked': 'True'}})
    return caravel_data if caravel else eval(x)


def select(x, options, caravel=False):
    assert isinstance(options, list), "options argument has to be a list, got '{}'.".format(type(options))
    caravel_data = attmap.AttMap({
                "element_type": "select",
                "element_args": {
                    "option": options
                }})
    return caravel_data if caravel else x
