import logging
import os
from .const import *
from .conductor import _get_yaml_path

_LOGGER = logging.getLogger(__name__)


def write_sample_yaml_prj(namespaces):
    """
    Plugin: saves sample representation with project reference to YAML.

    This plugin can be parametrized by providing the path value/template in
    'pipeline.var_templates.sample_yaml_prj_path'. This needs to be a complete and
    absolute path to the file where sample YAML representation is to be
    stored.

    :param dict namespaces: variable namespaces dict
    :return dict: sample namespace dict
    """
    sample = namespaces["sample"]
    sample.to_yaml(
        _get_yaml_path(namespaces, SAMPLE_YAML_PRJ_PATH_KEY, "_sample_prj"),
        add_prj_ref=True,
    )
    return {"sample": sample}


def write_custom_template(namespaces):
    """
    Plugin: Populates a user-provided jinja template

    Parameterize by providing pipeline.var_templates.custom_template
    """

    def load_template(pipeline):
        with open(namespaces["pipeline"]["var_templates"]["custom_template"], "r") as f:
            x = f.read()
        t = jinja2.Template(x)
        return t

    err_msg = (
        "Custom template plugin requires a template in var_templates.custom_template"
    )
    if "var_templates" not in namespaces["pipeline"].keys():
        _LOGGER.error(err_msg)
        return None

    if "custom_template" not in namespaces["pipeline"]["var_templates"].keys():
        _LOGGER.error(err_msg)
        return None

    import jinja2

    tpl = load_template(namespaces["pipeline"])
    content = tpl.render(namespaces)
    pth = _get_yaml_path(namespaces, "custom_template_output", "config")
    namespaces["sample"]["custom_template_output"] = pth
    with open(pth, "wb") as fh:
        # print(content)
        fh.write(content.encode())

    return {"sample": namespaces["sample"]}


def write_sample_yaml_cwl(namespaces):
    """
    Plugin: Produce a cwl-compatible yaml representation of the sample

    Also adds the 'cwl_yaml' attribute to sample objects, which points
    to the file produced.

    This plugin can be parametrized by providing the path value/template in
    'pipeline.var_templates.sample_cwl_yaml_path'. This needs to be a complete and
    absolute path to the file where sample YAML representation is to be
    stored.

    :param dict namespaces: variable namespaces dict
    :return dict: updated variable namespaces dict
    """
    from eido import read_schema
    from ubiquerg import is_url

    def _get_schema_source(
        schema_source, piface_dir=namespaces["looper"]["piface_dir"]
    ):
        # Stolen from piface object; should be a better way to do this...
        if is_url(schema_source):
            return schema_source
        elif not os.path.isabs(schema_source):
            schema_source = os.path.join(piface_dir, schema_source)
        return schema_source

    # To be compatible as a CWL job input, we need to handle the
    # File and Directory object types directly.
    sample = namespaces["sample"]
    sample.sample_yaml_cwl = _get_yaml_path(
        namespaces, SAMPLE_CWL_YAML_PATH_KEY, "_sample_cwl"
    )

    if "input_schema" in namespaces["pipeline"]:
        schema_path = _get_schema_source(namespaces["pipeline"]["input_schema"])
        file_list = []
        for ischema in read_schema(schema_path):
            if "files" in ischema["properties"]["samples"]["items"]:
                file_list.extend(ischema["properties"]["samples"]["items"]["files"])

        for file_attr in file_list:
            _LOGGER.debug("CWL-ing file attribute: {}".format(file_attr))
            file_attr_value = sample[file_attr]
            # file paths are assumed relative to the sample table;
            # but CWL assumes they are relative to the yaml output file,
            # so we convert here.
            file_attr_rel = os.path.relpath(
                file_attr_value, os.path.dirname(sample.sample_yaml_cwl)
            )
            sample[file_attr] = {"class": "File", "path": file_attr_rel}

        directory_list = []
        for ischema in read_schema(schema_path):
            if "directories" in ischema["properties"]["samples"]["items"]:
                directory_list.extend(
                    ischema["properties"]["samples"]["items"]["directories"]
                )

        for dir_attr in directory_list:
            _LOGGER.debug("CWL-ing directory attribute: {}".format(dir_attr))
            dir_attr_value = sample[dir_attr]
            # file paths are assumed relative to the sample table;
            # but CWL assumes they are relative to the yaml output file,
            # so we convert here.
            sample[dir_attr] = {"class": "Directory", "location": dir_attr_value}
    else:
        _LOGGER.warning(
            "No 'input_schema' defined, producing a regular "
            "sample YAML representation"
        )
    _LOGGER.info("Writing sample yaml to {}".format(sample.sample_yaml_cwl))
    sample.to_yaml(sample.sample_yaml_cwl)
    return {"sample": sample}


def write_sample_yaml(namespaces):
    """
    Plugin: saves sample representation to YAML.

    This plugin can be parametrized by providing the path value/template in
    'pipeline.var_templates.sample_yaml_path'. This needs to be a complete and
    absolute path to the file where sample YAML representation is to be
    stored.

    :param dict namespaces: variable namespaces dict
    :return dict: sample namespace dict
    """
    sample = namespaces["sample"]
    sample["sample_yaml_path"] = _get_yaml_path(
        namespaces, SAMPLE_YAML_PATH_KEY, "_sample"
    )
    sample.to_yaml(sample["sample_yaml_path"], add_prj_ref=False)
    return {"sample": sample}
