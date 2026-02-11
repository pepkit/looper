"""Definitions of the parser argument types"""

from yacman import YAMLConfigManager


def html_range(caravel=False, min_val=0, max_val=10, step=1, value=0):
    caravel_data = YAMLConfigManager(
        {
            "element_type": "range",
            "element_args": {
                "min": min_val,
                "max": max_val,
                "step": step,
                "value": value,
            },
        }
    )
    if step < 1:

        def fun(x=None, caravel_data=caravel_data, caravel=caravel):
            return caravel_data if caravel else float(x)

    else:

        def fun(x=None, caravel_data=caravel_data, caravel=caravel):
            return caravel_data if caravel else str(x)

    return fun


def html_checkbox(caravel=False, checked=False):
    """Create argument for type parameter on argparse.ArgumentParser.add_argument.

    Args:
        caravel (bool): Whether this is being used in the caravel context.
        checked (bool): Whether to add a particular key-value entry to a
            collection used by caravel.

    Returns:
        callable: Argument to the type parameter of an
            argparse.ArgumentParser's add_argument method.
    """
    caravel_data = YAMLConfigManager({"element_type": "checkbox", "element_args": {}})
    if checked:
        caravel_data.update({"element_args": {"checked": True}})

    def fun(x=None, caravel_data=caravel_data, caravel=caravel):
        return caravel_data if caravel else eval(x)

    return fun


def html_select(choices, caravel=False):
    """Create argument for type parameter on argparse.ArgumentParser.add_argument.

    Args:
        choices (list[object]): Collection of valid argument provisions via
            to a particular CLI option.
        caravel (bool): Whether this is being used in the caravel context.

    Returns:
        callable: Argument to the type parameter of an
            argparse.ArgumentParser's add_argument method.
    """
    if not isinstance(choices, list):
        raise TypeError(
            "Argument to choices parameter must be list, got {}.".format(type(choices))
        )
    caravel_data = YAMLConfigManager(
        {"element_type": "select", "element_args": {"option": choices}}
    )

    def fun(x=None, caravel_data=caravel_data, caravel=caravel):
        return caravel_data if caravel else x

    return fun
