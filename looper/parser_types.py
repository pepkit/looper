""" Definitions of the parser argument types """

from attmap import PathExAttMap


def html_range(caravel=False, min_val=0, max_val=10, step=1, value=0):
    caravel_data = PathExAttMap({
        "element_type": "range",
        "element_args": {
            "min": min_val, "max": max_val, "step": step, "value": value}})
    if step < 1:
        def fun(x=None, caravel_data=caravel_data, caravel=caravel):
            return caravel_data if caravel else float(x)
    else:
        def fun(x=None, caravel_data=caravel_data, caravel=caravel):
            return caravel_data if caravel else int(x)
    return fun


def html_checkbox(caravel=False):
    """
    Create argument for type parameter on argparse.ArgumentParser.add_argument.

    :param bool caravel: whether this is being used in the caravel context
    :return callable: argument to the type parameter of an
        argparse.ArgumentParser's add_argument method.
    :raise Exception: if attempting to add the checked flag who;e not indicating
        that the call is being made from a caravel context
    """
    caravel_data = PathExAttMap({"element_type": "checkbox", "element_args": {}})
    def fun(x=None, caravel_data=caravel_data, caravel=caravel):
        return caravel_data if caravel else eval(x)
    return fun


def html_select(choices, caravel=False):
    """
    Create argument for type parameter on argparse.ArgumentParser.add_argument.

    :param list[object] choices: collection of valid argument provisions via 
        to a particular CLI option
    :param bool caravel: whether this is being used in the caravel context
    :return callable: argument to the type parameter of an
        argparse.ArgumentParser's add_argument method.
    """
    if not isinstance(choices, list):
        raise TypeError(
            "Argument to choices parameter must be list, got {}.".format(type(choices)))
    caravel_data = PathExAttMap(
        {"element_type": "select", "element_args": {"option": choices}})
    def fun(x=None, caravel_data=caravel_data, caravel=caravel):
        return caravel_data if caravel else x
    return fun
