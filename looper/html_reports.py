""" Generate HTML reports """

import os
import glob
import pandas as _pd
import logging
import jinja2
import re
import sys
from warnings import warn
from datetime import timedelta
from json import dumps
from ._version import __version__ as v
from .const import *
from .processed_project import get_project_outputs
from .utils import get_file_for_project
from peppy.const import *
from eido import read_schema
from copy import copy as cp
_LOGGER = logging.getLogger("looper")


class HTMLReportBuilder(object):
    """ Generate HTML summary report for project/samples """

    def __init__(self, prj):
        """
        The Project defines the instance.

        :param Project prj: Project with which to work/operate on
        """
        super(HTMLReportBuilder, self).__init__()
        self.prj = prj
        self.j_env = get_jinja_env()
        self.reports_dir = get_file_for_project(self.prj, "reports")
        self.index_html_path = get_file_for_project(self.prj, "summary.html")
        self.index_html_filename = os.path.basename(self.index_html_path)
        self._outdir = self.prj.output_dir
        _LOGGER.debug(f"Reports dir: {self.reports_dir}")

    def __call__(self, pipeline_name):
        """ Do the work of the subcommand/program. """
        # Generate HTML report
        self.pipeline_name = pipeline_name
        selected_pipeline_pifaces = \
            [piface for piface in self.prj.pipeline_interfaces
             if piface.pipeline_name == self.pipeline_name]
        schema_path = self.prj.get_schemas(
            selected_pipeline_pifaces, OUTPUT_SCHEMA_KEY)[0]
        self.schema = read_schema(schema_path)[0]
        navbar = self.create_navbar(
            self.create_navbar_links(wd=self._outdir),
            self.index_html_filename
        )
        navbar_reports = self.create_navbar(
            self.create_navbar_links(wd=self.reports_dir),
            os.path.join(os.pardir, self.index_html_filename)
        )
        index_html_path = self.create_index_html(
            navbar, self.create_footer(), navbar_reports)
        return index_html_path

    def create_object_parent_html(self, navbar, footer):
        """
        Generates a page listing all the project objects with links
        to individual object pages

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent objects HTML file
        """
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        pages = list()
        labels = list()
        obj_result_ids = [k for k, _ in self.schema.items()
                          if self.schema[k]["type"] in OBJECT_TYPES]

        for key in obj_result_ids:
            desc = self.schema[key]["description"] \
                if "description" in self.schema[key] else ""
            labels.append(f"<b>{key.replace('_', ' ')}</b>: {desc}")
            page_path = os.path.join(
                self.reports_dir, self.pipeline_name, f"{key}.html".lower())
            pages.append(os.path.relpath(page_path, self.reports_dir))

        template_vars = dict(
            navbar=navbar, footer=footer, labels=labels,
            pages=pages, header="Objects"
        )
        return render_jinja_template(
            "navbar_list_parent.html", self.j_env, template_vars)

    def create_sample_parent_html(self, navbar, footer):
        """
        Generates a page listing all the project samples with links
        to individual sample pages
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent samples HTML file
        """
        sample_parent_path = os.path.join(
            self.reports_dir, self.pipeline_name, "samples.html")

        if not os.path.exists(os.path.dirname(sample_parent_path)):
            os.makedirs(os.path.dirname(sample_parent_path))
        pages = list()
        labels = list()
        for sample in self.prj.samples:
            sample_name = str(sample.sample_name)
            sample_dir = os.path.join(
                self.prj.results_folder, sample_name)

            # Confirm sample directory exists, then build page
            if os.path.exists(sample_dir):
                page_name = sample_name + ".html"
                page_path = os.path.join(
                    self.reports_dir, self.pipeline_name,
                    f"{sample_name}.html".replace(' ', '_').lower()
                )
                page_relpath = os.path.relpath(page_path, self.reports_dir)
                pages.append(page_relpath)
                labels.append(sample_name)

        template_vars = dict(navbar=navbar, footer=footer, labels=labels, pages=pages, header="Samples")
        return render_jinja_template("navbar_list_parent.html", self.j_env, template_vars)

    def create_navbar(self, navbar_links, index_html_relpath):
        """
        Creates the navbar using the privided links

        :param str navbar_links: HTML list of links to be inserted into a navbar
        :return str: navbar HTML
        """
        template_vars = dict(navbar_links=navbar_links, index_html=index_html_relpath)
        return render_jinja_template("navbar.html", self.j_env, template_vars)

    def create_footer(self):
        """
        Renders the footer from the templates directory

        :return str: footer HTML
        """
        return render_jinja_template("footer.html", self.j_env, dict(version=v))

    def create_navbar_links(self, wd=None, context=None, include_status=True):
        """
        Return a string containing the navbar prebuilt html.

        Generates links to each page relative to the directory of interest (wd arg) or uses the provided context to
        create the paths (context arg)

        :param path wd: the working directory of the current HTML page being generated, enables navbar links
            relative to page
        :param list[str] context: the context the links will be used in.
            The sequence of directories to be prepended to the HTML file in the resulting navbar
        :param bool include_status: whether the status link should be included in the links set
        :return str: navbar links as HTML-formatted string
        """
        # determine paths
        if wd is None and context is None:
            raise ValueError(
                "Either 'wd' (path the links should be relative to) or "
                "'context' (the context for the links) has to be provided.")
        status_relpath = _make_relpath(file_name=os.path.join(
            self.reports_dir, self.pipeline_name, "status.html"), wd=wd, context=context)
        objects_relpath = _make_relpath(file_name=os.path.join(
            self.reports_dir, self.pipeline_name, "objects.html"), wd=wd, context=context)
        samples_relpath = _make_relpath(file_name=os.path.join(
            self.reports_dir, self.pipeline_name, "samples.html"), wd=wd, context=context)
        # determine the outputs IDs by type
        obj_result_ids = {k: v for k, v in self.schema.items()
                          if self.schema[k]["type"] in OBJECT_TYPES}
        dropdown_keys_objects = None
        dropdown_relpaths_objects = None
        dropdown_relpaths_samples = None
        sample_names = None
        if len(obj_result_ids) > 0:
            # If the number of objects is 20 or less, use a drop-down menu
            if len(obj_result_ids) <= 20:
                dropdown_relpaths_objects, dropdown_keys_objects = \
                    self._get_navbar_dropdown_data_objects(
                        objs=obj_result_ids, wd=wd, context=context)
            else:
                dropdown_relpaths_objects = objects_relpath
        if len(self.prj.samples) >= 20:
            dropdown_relpaths_samples, sample_names = \
                self._get_navbar_dropdown_data_samples(wd=wd, context=context)
        else:
            # Create a menu link to the samples parent page
            dropdown_relpaths_samples = samples_relpath
        status_page_name = "Status" if include_status else None
        template_vars = dict(
            status_html_page=status_relpath, status_page_name=status_page_name,
            dropdown_keys_objects=dropdown_keys_objects, objects_page_name="Objects",
            samples_page_name="Samples", objects_html_page=dropdown_relpaths_objects,
            samples_html_page=dropdown_relpaths_samples, menu_name_objects="Objects",
            menu_name_samples="Samples", sample_names=sample_names, all_samples=samples_relpath,
            all_objects=objects_relpath
        )
        return render_jinja_template("navbar_links.html", self.j_env, template_vars)

    def create_object_htmls(self, navbar, footer):
        """
        Generates a page for an individual object type with all of its
        plots from each sample

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        """
        file_results = [k for k, v in self.schema.items()
                        if self.schema[k]["type"] == "file"]
        image_results = [k for k, v in self.schema.items()
                         if self.schema[k]["type"] == "image"]

        if not os.path.exists(os.path.dirname(self.reports_dir)):
            os.makedirs(os.path.dirname(self.reports_dir))

        links = []
        figures = []
        for file_result in file_results:
            html_page_path = os.path.join(
                self.reports_dir, self.pipeline_name, f"{file_result}.html".lower())
            for sample in self.prj.samples:
                sample_result = fetch_pipeline_results(
                    project=self.prj,
                    pipeline_name=self.pipeline_name,
                    sample_name=sample.sample_name
                )[file_result]
                links.append([sample.sample_name, sample_result["path"]])
            link_desc = self.schema[file_result]["description"] \
                if "description" in self.schema[file_result] else "No description in schema"
            template_vars = dict(
                navbar=navbar, footer=footer, name=sample_result["title"],
                figures=[], links=links, desc=link_desc
            )
            save_html(html_page_path, render_jinja_template(
                "object.html", self.j_env, args=template_vars))

        for image_result in image_results:
            html_page_path = os.path.join(
                self.reports_dir, f"{image_result}.html".lower())
            for sample in self.prj.samples:
                sample_result = fetch_pipeline_results(
                    project=self.prj,
                    pipeline_name=self.pipeline_name,
                    sample_name=sample.sample_name
                )[image_result]
                figures.append([sample_result["path"], sample.sample_name, sample_result["thumbnail_path"]])
            img_desc = self.schema[image_result]["description"] \
                if "description" in self.schema[image_result] else "No description in schema"
            template_vars = dict(
                navbar=navbar, footer=footer, name=sample_result["title"],
                figures=figures, links=[], desc=img_desc
            )
            save_html(html_page_path, render_jinja_template(
                "object.html", self.j_env, args=template_vars))

    def create_sample_html(self, sample_name, sample_stats, navbar, footer):
        """
        Produce an HTML page containing all of a sample's objects
        and the sample summary statistics

        :param str sample_name: the name of the current sample
        :param dict sample_stats: pipeline run statistics for the current sample
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: path to the produced HTML page
        """
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        html_page = os.path.join(
            self.reports_dir, self.pipeline_name, f"{sample_name}.html".lower())

        # single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
        sample_dir = os.path.join(self.prj.results_folder, sample_name)
        if os.path.exists(sample_dir):
            log_name = _get_file_for_sample(
                sample_name, f'{self.pipeline_name}_log.md', self.prj.results_folder)
            profile_name = _get_file_for_sample(
                sample_name, f'{self.pipeline_name}_profile.tsv', self.prj.results_folder)
            command_name = _get_file_for_sample(
                sample_name, f'{self.pipeline_name}_commands.sh', self.prj.results_folder)
            stats_name = "stats.tsv"
            # get links to the files
            stats_file_path = _get_relpath_to_file(
                stats_name, sample_name, self.prj.results_folder, self.reports_dir)
            profile_file_path = _get_relpath_to_file(
                profile_name, sample_name, self.prj.results_folder, self.reports_dir)
            commands_file_path = _get_relpath_to_file(
                command_name, sample_name, self.prj.results_folder, self.reports_dir)
            log_file_path = _get_relpath_to_file(
                log_name, sample_name, self.prj.results_folder, self.reports_dir)
            flag = _get_flags(sample_dir, self.pipeline_name)
            if not flag:
                button_class = "btn btn-secondary"
                flag = "Missing"
            elif len(flag) > 1:
                button_class = "btn btn-secondary"
                flag = "Multiple"
            else:
                flag = flag[0]
                try:
                    flag_dict = BUTTON_APPEARANCE_BY_FLAG[flag]
                except KeyError:
                    button_class = "btn btn-secondary"
                    flag = "Unknown"
                else:
                    button_class = flag_dict["button_class"]
                    flag = flag_dict["flag"]
        links = []
        file_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.pipeline_name,
            sample_name=sample_name,
            inclusion_fun=lambda x: x == "file"
        )
        for result_id, result in file_results.items():
            desc = self.schema[result_id]["description"] \
                if "description" in self.schema[result_id] else ""
            links.append([f"<b>{result['title']}</b>: {desc}", result["path"]])
        image_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.pipeline_name,
            sample_name=sample_name,
            inclusion_fun=lambda x: x == "image"
        )
        figures = []
        for result_id, result in image_results.items():
            figures.append([result["path"], result["title"], result["thumbnail_path"]])

        template_vars = dict(
            navbar=navbar, footer=footer, sample_name=sample_name,
            stats_file_path=stats_file_path, links=links,
            profile_file_path=profile_file_path,  figures=figures,
            commands_file_path=commands_file_path, log_file_path=log_file_path,
            button_class=button_class, sample_stats=sample_stats, flag=flag
        )
        save_html(html_page, render_jinja_template(
            "sample.html", self.j_env, template_vars))
        return os.path.relpath(html_page, self._outdir)

    def create_status_html(self, status_table, navbar, footer):
        """
        Generates a page listing all the samples, their run status, their
        log file, and the total runtime if completed.

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: rendered status HTML file
        """
        _LOGGER.debug("Building status page...")
        template_vars = dict(status_table=status_table, navbar=navbar,
                             footer=footer)
        return render_jinja_template("status.html", self.j_env, template_vars)

    def create_project_objects(self):
        """
        Render available project level outputs defined in the
        pipeline output schemas
        """
        # TODO: since a separate report is created from the
        #  project-level pipeline (?), some parts of sample.html creation
        #  can be abstracted and used here is is possible to treat project
        #  level pipeline results as a single sample?

        _LOGGER.debug("Building project objects section...")
        figures = []
        links = []
        warnings = []
        # For each protocol report the project summarizers' results
        self.prj.populate_pipeline_outputs()
        ifaces = self.prj.project_pipeline_interfaces
        # Check the interface files for summarizers
        for iface in ifaces:
            schema_paths = \
                iface.get_pipeline_schemas(OUTPUT_SCHEMA_KEY)
            if schema_paths is not None:
                if isinstance(schema_paths, str):
                    schema_paths = [schema_paths]
                for output_schema_path in schema_paths:
                    results = get_project_outputs(
                        self.prj, read_schema(output_schema_path))
                    for name, result in results.items():
                        title = str(result.setdefault('title', "No caption"))
                        result_type = str(result['type'])
                        result_file = str(result['path'])
                        result_img = \
                            str(result.setdefault('thumbnail_path', None))
                        if result_img and not os.path.isabs(result_file):
                            result_img = os.path.join(
                                self._outdir, result_img)
                        if not os.path.isabs(result_file):
                            result_file = os.path.join(
                                self._outdir, result_file)
                        _LOGGER.debug("Looking for project file: {}".
                                      format(result_file))
                        # Confirm the file itself was produced
                        if glob.glob(result_file):
                            file_path = str(glob.glob(result_file)[0])
                            file_relpath = \
                                os.path.relpath(file_path, self._outdir)
                            if result_type == "image":
                                # Add as a figure, find thumbnail
                                search = os.path.join(self._outdir, result_img)
                                if glob.glob(search):
                                    img_path = str(glob.glob(search)[0])
                                    img_relpath = \
                                        os.path.relpath(img_path, self._outdir)
                                    figures.append(
                                        [file_relpath, title, img_relpath])
                            # add as a link otherwise
                            # TODO: add more fine-grained type support?
                            #  not just image and link
                            else:
                                links.append([title, file_relpath])
                        else:
                            warnings.append("{} ({})".format(title,
                                                             result_file))
            else:
                _LOGGER.debug("No project-level outputs defined in "
                              "schema: {}".format(schema_paths))
        if warnings:
            _LOGGER.warning("Not found: {}".
                            format([str(x) for x in warnings]))
        _LOGGER.debug("collected project-level figures: {}".format(figures))
        _LOGGER.debug("collected project-level links: {}".format(links))
        template_vars = dict(figures=figures, links=links)
        return render_jinja_template("project_object.html", self.j_env,
                                     template_vars)

    def create_index_html(self, navbar, footer, navbar_reports=None):
        """
        Generate an index.html style project home page w/ sample summary
        statistics

        :param str navbar: HTML to be included as the navbar in the main
            summary page
        :param str footer: HTML to be included as the footer
        :param str navbar_reports: HTML to be included as the navbar for
            pages in the reports directory
        """
        # set default encoding when running in python2
        if sys.version[0] == '2':
            from importlib import reload
            reload(sys)
            sys.setdefaultencoding("utf-8")
        _LOGGER.info(f"Building index page for pipeline: {self.pipeline_name}")
        if navbar_reports is None:
            navbar_reports = navbar
        # Generate parent index.html page path
        index_html_path = get_file_for_project(
            self.prj, f"{self.pipeline_name}_summary.html")

        # Add stats_summary.tsv button link
        stats_file_name = os.path.join(self._outdir, self.prj.name)
        if hasattr(self.prj, "amendments") and self.prj.amendments:
            stats_file_name += '_' + self.prj.amendments
        stats_file_name += f'_{self.pipeline_name}_stats_summary.tsv'
        stats_file_path = os.path.relpath(stats_file_name, self._outdir)

        # Add stats summary table to index page and produce individual
        # sample pages
        # Produce table rows
        table_row_data = []
        _LOGGER.info(" * Creating sample pages")
        for sample in self.prj.samples:
            sample_stat_results = fetch_pipeline_results(
                project=self.prj,
                pipeline_name=self.pipeline_name,
                sample_name=sample.sample_name,
                inclusion_fun=lambda x: x not in OBJECT_TYPES,
                casting_fun=str
            )
            sample_page = self.create_sample_html(
                sample.sample_name, sample_stat_results, navbar_reports, footer)
            # treat sample_name column differently - will need to provide
            # a link to the sample page
            table_cell_data = [[sample_page, sample.sample_name]]
            table_cell_data += list(sample_stat_results.values())
            table_row_data.append(table_cell_data)
        # Create parent samples page with links to each sample
        save_html(
            path=os.path.join(self.reports_dir, self.pipeline_name, "samples.html"),
            template=self.create_sample_parent_html(navbar_reports, footer)
        )
        _LOGGER.info(" * Creating object pages")
        # Create objects pages
        self.create_object_htmls(navbar_reports, footer)

        # Create parent objects page with links to each object type
        save_html(
            path=os.path.join(self.reports_dir, self.pipeline_name, "objects.html"),
            template=self.create_object_parent_html(navbar_reports, footer)
        )
        # Create status page with each sample's status listed
        status_tab = create_status_table(
            prj=self.prj, final=True, pipeline_name=self.pipeline_name)
        save_html(
            path=os.path.join(self.reports_dir, self.pipeline_name, "status.html"),
            template=self.create_status_html(status_tab, navbar_reports, footer)
        )
        # Add project level objects
        # project_objects = self.create_project_objects()
        # Complete and close HTML file
        columns = [SAMPLE_NAME_ATTR] + list(sample_stat_results.keys())
        template_vars = dict(
            navbar=navbar, stats_file_path=stats_file_path,
            columns=columns, columns_json=dumps(columns),
            table_row_data=table_row_data, project_name=self.prj.name,
            stats_json=self._stats_to_json_str(project_level=False),
            footer=footer, pipeline_name=self.pipeline_name
        )
        save_html(index_html_path, render_jinja_template(
            "index.html", self.j_env, template_vars))
        return index_html_path

    def _stats_to_json_str(self, project_level=False):
        results = {}
        if project_level:
            results[self.prj.name] = fetch_pipeline_results(
                project=self.prj,
                pipeline_name=self.pipeline_name,
                inclusion_fun=lambda x: x not in OBJECT_TYPES,
                casting_fun=str
            )
        else:
            for sample in self.prj.samples:
                results[sample.sample_name] = fetch_pipeline_results(
                    project=self.prj,
                    sample_name=sample.sample_name,
                    pipeline_name=self.pipeline_name,
                    inclusion_fun=lambda x: x not in OBJECT_TYPES,
                    casting_fun=str
                )
        return dumps(results)

    def _get_navbar_dropdown_data_objects(self, objs, wd, context):
        if objs is None or len(objs) == 0:
            return None, None
        relpaths = []
        displayable_ids = []
        for obj_id in objs:
            displayable_ids.append(obj_id.replace('_', ' '))
            page_name = os.path.join(
                self.reports_dir,
                self.pipeline_name, (obj_id + ".html").replace(' ', '_').lower()
            )
            relpaths.append(_make_relpath(page_name, wd, context))
        return relpaths, displayable_ids

    def _get_navbar_dropdown_data_samples(self, wd, context):
        relpaths = []
        sample_names = []
        for sample in self.prj.samples:
            page_name = os.path.join(
                self.reports_dir, self.pipeline_name,
                f"{sample.sample_name}.html".replace(' ', '_').lower()
            )
            relpaths.append(_make_relpath(page_name, wd, context))
            sample_names.append(sample.sample_name)
        return relpaths, sample_names


def render_jinja_template(name, jinja_env, args=dict()):
    """
    Render template in the specified jinja environment using the provided args

    :param str name: name of the template
    :param dict args: arguments to pass to the template
    :param jinja2.Environment jinja_env: the initialized environment to use in
        this the looper HTML reports context
    :return str: rendered template
    """
    assert isinstance(args, dict), "args has to be a dict"
    template = jinja_env.get_template(name)
    return template.render(**args)


def save_html(path, template):
    """
    Save rendered template as an HTML file

    :param str path: the desired location for the file to be produced
    :param str template: the template or just string
    """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    try:
        with open(path, 'w') as f:
            f.write(template)
    except IOError:
        _LOGGER.error("Could not write the HTML file: {}".format(path))


def get_jinja_env(templates_dirname=None):
    """
    Create jinja environment with the provided path to the templates directory

    :param str templates_dirname: path to the templates directory
    :return jinja2.Environment: jinja environment
    """
    if templates_dirname is None:
        file_dir = os.path.dirname(os.path.realpath(__file__))
        templates_dirname = os.path.join(file_dir, TEMPLATES_DIRNAME)
    _LOGGER.debug("Using templates dir: " + templates_dirname)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dirname))


def _get_flags(sample_dir, pipeline_name):
    """
    Get the flag(s) present in the directory

    :param str sample_dir: path to the directory to be searched for flags
    :return list: flags found in the dir
    """
    assert os.path.exists(sample_dir), \
        f"The provided path ({sample_dir}) does not exist"
    template = os.path.join(sample_dir, f'{pipeline_name}_{{}}.flag')
    flag_paths_by_flag = {f: template.format(f) for f in FLAGS}
    existing_flags = [k for k, v in flag_paths_by_flag.items()
                      if os.path.exists(v)]
    if len(existing_flags) > 1:
        _LOGGER.warning(
            f"Multiple flag files ({len(existing_flags)}) found in: {sample_dir}")
    if len(existing_flags) == 0:
        _LOGGER.warning(f"No flag files found in sample dir '{sample_dir}'")
    return existing_flags


def _get_file_for_sample(sample_name, appendix, location, full_path=False):
    """
    Safely looks for files matching the appendix in the specified
    location for the sample

    :param str sample_name: name of the sample that the file name
        should be found for
    :param str appendix: the ending  specific for the file
    :param str location: where to look for the file
    :param bool full_path: whether to return full path
    :return str: the name of the matched file
    """
    filepath = os.path.join(location, sample_name, appendix)
    if os.path.exists(filepath):
        return filepath if full_path else os.path.basename(filepath)
    raise FileNotFoundError(filepath)


def _get_relpath_to_file(file_name, sample_name, location, relative_to):
    """
    Safely gets the relative path for the file for the specified sample

    :param str file_name: name of the file
    :param str sample_name: name of the sample that the file path
        should be found for
    :param str location: where to look for the file
    :param str relative_to: path the result path should be relative to
    :return str: a path to the file
    """
    abs_file_path = os.path.join(location, sample_name, file_name)
    rel_file_path = os.path.relpath(abs_file_path, relative_to)
    if file_name is None or not os.path.exists(abs_file_path):
        return None
    return rel_file_path


def _make_relpath(file_name, wd, context=None):
    """
    Create a path relative to the context. This function introduces the
    flexibility to the navbar links creation, which the can be used outside
    of the native looper summary pages.

    :param str file_name: the path to make relative
    :param str wd: the dir the path should be relative to
    :param list[str] context: the context the links will be used in. The
        sequence of directories to be prepended to the HTML
        file in the resulting navbar
    :return str: relative path
    """
    relpath = os.path.relpath(file_name, wd)
    return relpath if not context \
        else os.path.join(os.path.join(*context), relpath)


def _read_csv_encodings(path, encodings=["utf-8", "ascii"], **kwargs):
    """
    Try to read file with the provided encodings

    :param str path: path to file
    :param list encodings: list of encodings to try
    """
    idx = 0
    while idx < len(encodings):
        e = encodings[idx]
        try:
            t = _pd.read_csv(path, encoding=e, **kwargs)
            return t
        except UnicodeDecodeError:
            pass
        idx = idx + 1
    _LOGGER.warning(
        f"Could not read the log file '{path}' with encodings '{encodings}'")


def _read_tsv_to_json(path):
    """
    Read a tsv file to a JSON formatted string

    :param path: to file path
    :return str: JSON formatted string
    """
    assert os.path.exists(path), "The file '{}' does not exist".format(path)
    _LOGGER.debug("Reading TSV from '{}'".format(path))
    df = _pd.read_csv(path, sep="\t", index_col=False, header=None)
    return df.to_json()

def fetch_pipeline_results(project, pipeline_name, sample_name=None,
                           inclusion_fun=None, casting_fun=None):
    """
    Get the specific pipeline results for sample based on inclusion function

    :param looper.Project project: project to get the results for
    :param str pipeline_name: pipeline ID
    :param str sample_name: sample ID
    :param callable(str) inclusion_fun: a function that determines whether the
        result should be returned based on it's type. Example input that the
        function will be fed with is: 'image' or 'integer'
    :param callable(str) casting_fun: a function that will be used to cast the
        each of the results to a proper type before returning, e.g int, str
    :return dict: selected pipeline results
    """
    psms = project.get_pipestat_managers(
        sample_name=sample_name,
        project_level=sample_name is None
    )
    if pipeline_name not in psms:
        _LOGGER.warning(
            f"Pipeline name '{pipeline_name}' not found in "
            f"{list(psms.keys())}. This pipeline was not run for"
            f" sample: {sample_name}"
        )
        return
    # set defaults to arg functions
    pass_all_fun = lambda x: x
    inclusion_fun = inclusion_fun or pass_all_fun
    casting_fun = casting_fun or pass_all_fun
    psm = psms[pipeline_name]
    # exclude object-like results from the stats results mapping
    rep_data = psm.data[psm.namespace][psm.record_identifier].items()
    results = {k: casting_fun(v) for k, v in rep_data
               if k in psm.schema and inclusion_fun(psm.schema[k]["type"])}
    return results


def uniqify(seq):
    """ Fast way to uniqify while preserving input order. """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def create_status_table(prj, pipeline_name, final=True):
    """
    Creates status table, the core of the status page.
    It is abstracted into a function so that it can be used in other software
    packages. It can produce a table of two types. With links to the
    samples/log files and without. The one without can be used to render HTMLs
     for on-th-fly job status inspection.

    :param looper.Project prj: project to create the status table for
    :param bool final: if the status table is created for a finalized looper
        run. In such a case, links to samples and log files will be provided
    :return str: rendered status HTML file
    """
    status_warning = False
    sample_warning = []
    log_paths = []
    log_link_names = []
    sample_paths = []
    sample_link_names = []
    flags = []
    row_classes = []
    times = []
    mems = []
    for sample in prj.samples:
        sample_name = str(sample.sample_name)
        sample_dir = os.path.join(
            prj.results_folder, sample_name)

        # Confirm sample directory exists, then build page
        if os.path.exists(sample_dir):
            # Grab the status flag for the current sample
            flag = _get_flags(sample_dir, pipeline_name)
            if not flag:
                button_class = "table-secondary"
                flag = "Missing"
            elif len(flag) > 1:
                button_class = "table-secondary"
                flag = "Multiple"
            else:
                flag = flag[0]
                try:
                    flag_dict = TABLE_APPEARANCE_BY_FLAG[flag]
                except KeyError:
                    button_class = "table-secondary"
                    flag = "Unknown"
                else:
                    button_class = flag_dict["button_class"]
                    flag = flag_dict["flag"]
            row_classes.append(button_class)
            # get first column data (sample name/link)
            page_name = sample_name + ".html"
            page_path = os.path.join(
                get_file_for_project(prj, "reports"), pipeline_name, page_name.replace(' ', '_').lower())
            page_relpath = os.path.relpath(page_path, get_file_for_project(prj, "reports"))
            sample_paths.append(page_relpath)
            sample_link_names.append(sample_name)
            # get second column data (status/flag)
            flags.append(flag)
            # get third column data (log file/link)
            log_name = _get_file_for_sample(
                sample_name, f"{pipeline_name}_log.md", prj.results_folder)
            log_file_link = _get_relpath_to_file(
                log_name, sample_name, prj.results_folder, get_file_for_project(prj, "reports"))
            log_link_names.append(log_name)
            log_paths.append(log_file_link)
            # get fourth column data (runtime) and fifth column data (memory)
            profile_file_path = \
                _get_file_for_sample(sample.sample_name, f'{pipeline_name}_profile.tsv',
                                     prj.results_folder, full_path=True)
            if os.path.exists(profile_file_path):
                df = _pd.read_csv(profile_file_path, sep="\t", comment="#",
                                  names=PROFILE_COLNAMES)
                df['runtime'] = _pd.to_timedelta(df['runtime'])
                times.append(_get_runtime(df))
                mems.append(_get_maxmem(df))
            else:
                _LOGGER.warning("'{}' does not exist".format(profile_file_path))
                times.append(NO_DATA_PLACEHOLDER)
                mems.append(NO_DATA_PLACEHOLDER)
        else:
            # Sample was not run through the pipeline
            sample_warning.append(sample_name)

    # Alert the user to any warnings generated
    if status_warning:
        _LOGGER.warning("The stats table is incomplete, likely because one or "
                        "more jobs either failed or is still running.")
    if sample_warning:
        _LOGGER.warning("{} samples not present in {}: {}".format(
            len(sample_warning), prj.results_folder,
            str([sample for sample in sample_warning])))
    template_vars = dict(sample_link_names=sample_link_names,
                         row_classes=row_classes, flags=flags, times=times,
                         mems=mems)
    template_name = "status_table_no_links.html"
    if final:
        template_name = "status_table.html"
        template_vars.update(dict(sample_paths=sample_paths,
                                  log_link_names=log_link_names,
                                  log_paths=log_paths))
    return render_jinja_template(template_name, get_jinja_env(), template_vars)


def _get_maxmem(profile):
    """
    Get current peak memory

    :param pandas.core.frame.DataFrame profile: a data frame representing
        the current profile.tsv for a sample
    :return str: max memory
    """
    return f"{str(max(profile['mem']) if not profile['mem'].empty else 0)} GB"


def _get_runtime(profile_df):
    """
    Collect the unique and last duplicated runtimes, sum them and then
    return in str format

    :param pandas.core.frame.DataFrame profile_df: a data frame representing
        the current profile.tsv for a sample
    :return str: sum of runtimes
    """
    unique_df = profile_df[~profile_df.duplicated('cid', keep='last').values]
    return str(timedelta(seconds=sum(unique_df['runtime'].apply(
        lambda x: x.total_seconds())))).split(".")[0]
