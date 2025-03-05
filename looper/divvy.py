"""Computing configuration representation"""

import logging
import os
import shutil


from shutil import copytree
from yacman import FutureYAMLConfigManager as YAMLConfigManager
from yacman import write_lock, FILEPATH_KEY, load_yaml, select_config


from .const import (
    COMPUTE_SETTINGS_VARNAME,
    DEFAULT_COMPUTE_RESOURCES_NAME,
    NEW_COMPUTE_KEY,
    DEFAULT_CONFIG_FILEPATH,
    DEFAULT_CONFIG_SCHEMA,
)
from .utils import write_submit_script


_LOGGER = logging.getLogger(__name__)

# This is the divvy.py submodule from divvy


class ComputingConfiguration(YAMLConfigManager):
    """
    Represents computing configuration objects.

    The ComputingConfiguration class provides a computing configuration object
    that is an *in memory* representation of a `divvy` computing configuration
    file. This object has various functions to allow a user to activate, modify,
    and retrieve computing configuration files, and use these values to populate
    job submission script templates.

    :param str | Iterable[(str, object)] | Mapping[str, object] entries: config
        Collection of key-value pairs.
    :param str filepath: YAML file specifying computing package data. (the
        `DIVCFG` file)
    """

    def __init__(
        self,
        entries=None,
        wait_max=None,
        strict_ro_locks=False,
        schema_source=None,
        validate_on_write=False,
    ):
        super().__init__(
            entries, wait_max, strict_ro_locks, schema_source, validate_on_write
        )

        if "compute_packages" not in self:
            self["compute_packages"] = {}
        # Initialize default compute settings.
        _LOGGER.debug("Establishing project compute settings")
        self.compute = None
        self.setdefault("adapters", None)
        self.activate_package(DEFAULT_COMPUTE_RESOURCES_NAME)

    def write(self, filename=None):
        with write_lock(self) as locked_ym:
            locked_ym.rebase()
            locked_ym.write()
        filename = filename or getattr(self, FILEPATH_KEY)
        filedir = os.path.dirname(filename)
        # For this object, we *also* have to write the template files
        for pkg_name, pkg in self["compute_packages"].items():
            print(pkg)
            destfile = os.path.join(filedir, os.path.basename(pkg.submission_template))
            shutil.copyfile(pkg.submission_template, destfile)

    @property
    def compute_env_var(self):
        """
        Environment variable through which to access compute settings.

        :return list[str]: names of candidate environment variables, for which
            value may be path to compute settings file; first found is used.
        """
        return COMPUTE_SETTINGS_VARNAME

    @property
    def default_config_file(self):
        """
        Path to default compute environment settings file.

        :return str: Path to default compute settings file
        """
        return DEFAULT_CONFIG_FILEPATH

    # Warning: template cannot be a property, because otherwise
    # it will get treated as a PathExAttMap treats all properties, which
    # is that it will turn any double-slashes into single slashes.
    def template(self):
        """
        Get the currently active submission template.

        :return str: submission script content template for current state
        """
        with open(self.compute["submission_template"], "r") as f:
            return f.read()

    @property
    def templates_folder(self):
        """
        Path to folder with default submission templates.

        :return str: path to folder with default submission templates
        """
        if self.filepath:
            return os.path.join(os.path.dirname(self.filepath), "divvy_templates")
        else:
            return os.path.join(
                os.path.dirname(__file__), "default_config", "divvy_templates"
            )

    def activate_package(self, package_name):
        """
        Activates a compute package.

        This copies the computing attributes from the configuration file into
        the `compute` attribute, where the class stores current compute
        settings.

        :param str package_name: name for non-resource compute bundle,
            the name of a subsection in an environment configuration file
        :return bool: success flag for attempt to establish compute settings
        """

        # Hope that environment & environment compute are present.
        act_msg = "Activating compute package '{}'".format(package_name)
        if package_name == "default":
            _LOGGER.debug(act_msg)
        else:
            _LOGGER.info(act_msg)

        if (
            package_name
            and self["compute_packages"]
            and package_name in self["compute_packages"]
        ):
            # Augment compute, creating it if needed.
            if self.compute is None:
                _LOGGER.debug("Creating Project compute")
                self.compute = YAMLConfigManager()
                _LOGGER.debug(
                    "Adding entries for package_name '{}'".format(package_name)
                )

            self.compute.update_from_obj(self["compute_packages"][package_name])

            # Ensure submission template is absolute. This *used to be* handled
            # at update (so the paths were stored as absolutes in the packages),
            # but now, it makes more sense to do it here so we can piggyback on
            # the default update() method and not even have to do that.
            if not os.path.isabs(self.compute["submission_template"]):

                try:
                    if self.filepath:
                        self.compute["submission_template"] = os.path.join(
                            os.path.dirname(self.filepath),
                            self.compute["submission_template"],
                        )
                    else:
                        self.compute["submission_template"] = os.path.join(
                            os.path.dirname(self.default_config_file),
                            self.compute["submission_template"],
                        )
                except AttributeError as e:
                    # Environment and environment compute should at least have been
                    # set as null-valued attributes, so execution here is an error.
                    _LOGGER.error(str(e))

            _LOGGER.debug(
                "Submit template set to: {}".format(self.compute["submission_template"])
            )

            return True

        else:
            # Scenario in which environment and environment compute are
            # both present--but don't evaluate to True--is fairly harmless.
            _LOGGER.debug(
                "Can't activate package. compute_packages = {}".format(
                    self["compute_packages"]
                )
            )

        return False

    def clean_start(self, package_name):
        """
        Clear current active settings and then activate the given package.

        :param str package_name: name of the resource package to activate
        :return bool: success flag
        """
        self.reset_active_settings()
        return self.activate_package(package_name)

    def get_active_package(self) -> YAMLConfigManager:
        """
        Returns settings for the currently active compute package

        :return YAMLConfigManager: data defining the active compute package
        """
        return self.compute

    @property
    def compute_packages(self):

        return self["compute_packages"]

    def list_compute_packages(self):
        """
        Returns a list of available compute packages.

        :return set[str]: names of available compute packages
        """
        return set(self["compute_packages"].keys())

    def reset_active_settings(self):
        """
        Clear out current compute settings.

        :return bool: success flag
        """
        self.compute = YAMLConfigManager()
        return True

    def update_packages(self, config_file):
        """
        Parse data from divvy configuration file.

        Given a divvy configuration file, this function will update (not
        overwrite) existing compute packages with existing values. It does not
        affect any currently active settings.

        :param str config_file: path to file with new divvy configuration data
        """
        entries = load_yaml(config_file)
        self.update(entries)
        return True

    def get_adapters(self) -> YAMLConfigManager:
        """
        Get current adapters, if defined.

        Adapters are sourced from the 'adapters' section in the root of the
        divvy configuration file and updated with an active compute
        package-specific set of adapters, if any defined in 'adapters' section
        under currently active compute package.

        :return YAMLConfigManager: current adapters mapping
        """
        adapters = YAMLConfigManager()
        if "adapters" in self and self["adapters"] is not None:
            adapters.update(self["adapters"])
        if "compute" in self and "adapters" in self.compute:
            adapters.update(self.compute["adapters"])
        if not adapters:
            _LOGGER.debug("No adapters determined in divvy configuration file.")
        return adapters

    def submit(self, output_path, extra_vars=None):
        if not output_path:
            import tempfile

            with tempfile.NamedTemporaryFile() as temp:
                _LOGGER.info(
                    "No file provided; using temp file: '{}'".format(temp.name)
                )
                self.submit(temp.name, extra_vars)
        else:
            script = self.write_script(output_path, extra_vars)
            submission_command = "{} {}".format(
                self.compute["submission_command"], script
            )
            _LOGGER.info(submission_command)
            os.system(submission_command)

    def write_script(self, output_path, extra_vars=None):
        """
        Given currently active settings, populate the active template to write a
         submission script. Additionally use the current adapters to adjust
         the select of the provided variables

        :param str output_path: Path to file to write as submission script
        :param Iterable[Mapping] extra_vars: A list of Dict objects with
            key-value pairs with which to populate template fields. These will
            override any values in the currently active compute package.
        :return str: Path to the submission script file
        """

        def _get_from_dict(map, attrs):
            """
            Get value from a possibly mapping using a list of its attributes

            :param collections.Mapping map: mapping to retrieve values from
            :param Iterable[str] attrs: a list of attributes
            :return: value found in the the requested attribute or
                None if one of the keys does not exist
            """
            for a in attrs:
                try:
                    map = map[a]
                except KeyError:
                    return None
            return map

        from copy import deepcopy

        variables = deepcopy(self.compute)
        _LOGGER.debug("Extra vars: {}".format(extra_vars))
        if extra_vars:
            if not isinstance(extra_vars, list):
                extra_vars = [extra_vars]
            adapters = self.get_adapters()
            exclude = set()
            if adapters:
                # apply adapted values first and keep track of
                # which of extra_vars were used
                for n, v in adapters.items():
                    split_v = v.split(".")
                    namespace = split_v[0]
                    for extra_var in reversed(extra_vars):
                        if (
                            len(extra_var) > 0
                            and namespace in list(extra_var.keys())[0]
                        ):
                            exclude.add(namespace)
                            var = _get_from_dict(extra_var, split_v)
                            if var is not None:
                                variables[n] = var
                                _LOGGER.debug(
                                    "adapted {}: ({}={})".format(
                                        n, ".".join(split_v), var
                                    )
                                )
            for extra_var in reversed(extra_vars):
                # then update variables with the rest of the extra_vars
                if len(extra_var) > 0 and list(extra_var.keys())[0] not in exclude:
                    variables.update(extra_var)
        _LOGGER.debug(
            "Submission template: {}".format(self.compute["submission_template"])
        )
        if output_path:
            _LOGGER.info("Writing script to {}".format(os.path.abspath(output_path)))

        return write_submit_script(output_path, self.template(), variables)

    def _handle_missing_env_attrs(self, config_file, when_missing):
        """Default environment settings aren't required; warn, though."""
        missing_env_attrs = [
            attr
            for attr in [NEW_COMPUTE_KEY, "config_file"]
            if getattr(self, attr, None) is None
        ]
        if not missing_env_attrs:
            return
        message = "'{}' lacks environment attributes: {}".format(
            config_file, missing_env_attrs
        )
        if when_missing is None:
            _LOGGER.warning(message)
        else:
            when_missing(message)


def select_divvy_config(filepath):
    """
    Selects the divvy config file path to load.

    This uses a priority ordering to first choose a config file path if
    it's given, but if not, then look in a priority list of environment
    variables and choose the first available file path to return. If none of
    these options succeed, the default config path will be returned.

    :param str | NoneType filepath: direct file path specification
    :return str: path to the config file to read
    """
    divcfg = select_config(
        config_filepath=filepath,
        config_env_vars=COMPUTE_SETTINGS_VARNAME,
        default_config_filepath=DEFAULT_CONFIG_FILEPATH,
        check_exist=True,
        config_name="divvy",
    )
    _LOGGER.debug("Selected divvy config: {}".format(divcfg))
    return divcfg


def divvy_init(config_path, template_config_path):
    """
    Initialize a genome config file.

    :param str config_path: path to divvy configuration file to
        create/initialize
    :param str template_config_path: path to divvy configuration file to
        copy FROM
    """
    if not config_path:
        _LOGGER.error("You must specify a file path to initialize.")
        return

    if not template_config_path:
        _LOGGER.error("You must specify a template config file path.")
        return

    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    if config_path and not os.path.exists(config_path):
        # Init should *also* write the templates.
        dest_folder = os.path.dirname(config_path)
        copytree(os.path.dirname(template_config_path), dest_folder, dirs_exist_ok=True)
        template_subfolder = os.path.join(dest_folder, "divvy_templates")
        _LOGGER.info("Wrote divvy templates to folder: {}".format(template_subfolder))
        new_template = os.path.join(
            os.path.dirname(config_path), os.path.basename(template_config_path)
        )
        os.rename(new_template, config_path)
        _LOGGER.info("Wrote new divvy configuration file: {}".format(config_path))
    else:
        _LOGGER.warning("Can't initialize, file exists: {} ".format(config_path))
