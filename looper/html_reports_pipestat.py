""" Generate HTML reports """

import glob
import logging
import os
import re
import sys
from copy import copy as cp
from datetime import timedelta
from json import dumps
from warnings import warn

import jinja2
import pandas as _pd
from eido import read_schema
from peppy.const import *

from ._version import __version__ as v
from .const import *
from .processed_project import get_project_outputs
from .utils import get_file_for_project

_LOGGER = logging.getLogger("looper")


class HTMLReportBuilder(object):
    """Generate HTML summary report for project/samples"""

    def __init__(self, prj):
        """
        The Project defines the instance.

        :param looper.Project prj: Project with which to work/operate on
        """
        super(HTMLReportBuilder, self).__init__()
        self.prj = prj
        self.j_env = get_jinja_env()
        self.output_dir = self.prj.output_dir
        self.reports_dir = os.path.join(self.output_dir, "reports")
        _LOGGER.debug(f"Reports dir: {self.reports_dir}")

    def __call__(self, pipeline_name, project_index_html=None):
        """
        Generate HTML report.

        :param str pipeline_name: ID of the pipeline to generate the report for
        :return str: path to the index page of the generated HTML report
        """
        # Generate HTML report
        self.pipeline_name = pipeline_name
        self.amendments_str = (
            "_".join(self.prj.amendments) if self.prj.amendments else ""
        )
        self.pipeline_reports = os.path.join(
            self.reports_dir,
            f"{self.pipeline_name}_{self.amendments_str}"
            if self.prj.amendments
            else self.pipeline_name,
        )
        self.prj_index_html_path = project_index_html
        self.index_html_path = os.path.join(self.pipeline_reports, "index.html")
        pifaces = self.prj.pipeline_interfaces
        selected_pipeline_pifaces = [
            p for p in pifaces if p.pipeline_name == self.pipeline_name
        ]
        schema_path = self.prj.get_schemas(
            selected_pipeline_pifaces, OUTPUT_SCHEMA_KEY
        )[0]
        self.schema = read_schema(schema_path)[0]
        navbar = self.create_navbar(
            navbar_links=self.create_navbar_links(
                wd=self.pipeline_reports,
                project_index_html_relpath=os.path.relpath(
                    self.prj_index_html_path, self.pipeline_reports
                )
                if self.prj_index_html_path
                else None,
            ),
            index_html_relpath=os.path.relpath(
                self.index_html_path, self.pipeline_reports
            ),
        )
        self.create_index_html(navbar, self.create_footer())
        return self.index_html_path

    def create_object_parent_html(self, navbar, footer):
        """
        Generates a page listing all the project objects with links
        to individual object pages

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent objects HTML file
        """
        if not os.path.exists(self.pipeline_reports):
            os.makedirs(self.pipeline_reports)
        pages = list()
        labels = list()
        obj_result_ids = self.get_nonhighlighted_results(OBJECT_TYPES)

        for key in obj_result_ids:
            desc = (
                self.schema[key]["description"]
                if "description" in self.schema[key]
                else ""
            )
            labels.append(f"<b>{key.replace('_', ' ')}</b>: {desc}")
            page_path = os.path.join(self.pipeline_reports, f"{key}.html".lower())
            pages.append(os.path.relpath(page_path, self.pipeline_reports))

        template_vars = dict(
            navbar=navbar, footer=footer, labels=labels, pages=pages, header="Objects"
        )
        _LOGGER.debug(
            f"object navbar_list_parent.html | template_vars:" f"\n{template_vars}"
        )
        return render_jinja_template(
            "navbar_list_parent.html", self.j_env, template_vars
        )

    def create_sample_parent_html(self, navbar, footer):
        """
        Generates a page listing all the project samples with links
        to individual sample pages
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent samples HTML file
        """
        if not os.path.exists(self.pipeline_reports):
            os.makedirs(self.pipeline_reports)
        pages = list()
        labels = list()
        for sample in self.prj.samples:
            sample_name = str(sample.sample_name)
            sample_dir = os.path.join(self.prj.results_folder, sample_name)

            # Confirm sample directory exists, then build page
            if os.path.exists(sample_dir):
                page_path = os.path.join(
                    self.pipeline_reports,
                    f"{sample_name}.html".replace(" ", "_").lower(),
                )
                page_relpath = os.path.relpath(page_path, self.pipeline_reports)
                pages.append(page_relpath)
                labels.append(sample_name)

        template_vars = dict(
            navbar=navbar, footer=footer, labels=labels, pages=pages, header="Samples"
        )
        _LOGGER.debug(
            f"sample navbar_list_parent.html | template_vars:" f"\n{template_vars}"
        )
        return render_jinja_template(
            "navbar_list_parent.html", self.j_env, template_vars
        )

    def create_navbar(self, navbar_links, index_html_relpath):
        """
        Creates the navbar using the provided links

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

    def create_navbar_links(
        self, wd=None, context=None, project_index_html_relpath=None
    ):
        """
        Return a string containing the navbar prebuilt html.

        Generates links to each page relative to the directory of interest
        (wd arg) or uses the provided context to create the paths (context arg)

        :param path wd: the working directory of the current HTML page being
            generated, enables navbar links relative to page
        :param list[str] context: the context the links will be used in.
            The sequence of directories to be prepended to the HTML file in
            the resulting navbar
        :return str: navbar links as HTML-formatted string
        """
        # determine paths
        if wd is None and context is None:
            raise ValueError(
                "Either 'wd' (path the links should be relative to) or "
                "'context' (the context for the links) has to be provided."
            )
        status_relpath = _make_relpath(
            file_name=os.path.join(self.pipeline_reports, "status.html"),
            wd=wd,
            context=context,
        )
        objects_relpath = _make_relpath(
            file_name=os.path.join(self.pipeline_reports, "objects.html"),
            wd=wd,
            context=context,
        )
        samples_relpath = _make_relpath(
            file_name=os.path.join(self.pipeline_reports, "samples.html"),
            wd=wd,
            context=context,
        )
        # determine the outputs IDs by type
        obj_result_ids = self.get_nonhighlighted_results(OBJECT_TYPES)
        dropdown_keys_objects = None
        dropdown_relpaths_objects = None
        sample_names = None
        if len(obj_result_ids) > 0:
            # If the number of objects is 20 or less, use a drop-down menu
            if len(obj_result_ids) <= 20:
                (
                    dropdown_relpaths_objects,
                    dropdown_keys_objects,
                ) = self._get_navbar_dropdown_data_objects(
                    objs=obj_result_ids, wd=wd, context=context
                )
        else:
            dropdown_relpaths_objects = objects_relpath
        if len(self.prj.samples) <= 20:
            (
                dropdown_relpaths_samples,
                sample_names,
            ) = self._get_navbar_dropdown_data_samples(wd=wd, context=context)
        else:
            # Create a menu link to the samples parent page
            dropdown_relpaths_samples = samples_relpath
        template_vars = dict(
            status_html_page=status_relpath,
            status_page_name="Status",
            dropdown_keys_objects=dropdown_keys_objects,
            objects_page_name="Objects",
            samples_page_name="Samples",
            objects_html_page=dropdown_relpaths_objects,
            samples_html_page=dropdown_relpaths_samples,
            menu_name_objects="Objects",
            menu_name_samples="Samples",
            sample_names=sample_names,
            all_samples=samples_relpath,
            all_objects=objects_relpath,
            sample_reports_parent=None,
            project_report=project_index_html_relpath,
        )
        _LOGGER.debug(f"navbar_links.html | template_vars:\n{template_vars}")
        return render_jinja_template("navbar_links.html", self.j_env, template_vars)

    def create_object_htmls(self, navbar, footer):
        """
        Generates a page for an individual object type with all of its
        plots from each sample

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        """
        file_results = self.get_nonhighlighted_results(["file"])
        image_results = self.get_nonhighlighted_results(["image"])

        if not os.path.exists(self.pipeline_reports):
            os.makedirs(self.pipeline_reports)
        for file_result in file_results:
            links = []
            html_page_path = os.path.join(
                self.pipeline_reports, f"{file_result}.html".lower()
            )
            for sample in self.prj.samples:
                sample_result = fetch_pipeline_results(
                    project=self.prj,
                    pipeline_name=self.pipeline_name,
                    sample_name=sample.sample_name,
                )
                if file_result not in sample_result:
                    break
                sample_result = sample_result[file_result]
                links.append(
                    [
                        sample.sample_name,
                        os.path.relpath(sample_result["path"], self.pipeline_reports),
                    ]
                )
            else:
                link_desc = (
                    self.schema[file_result]["description"]
                    if "description" in self.schema[file_result]
                    else "No description in schema"
                )
                template_vars = dict(
                    navbar=navbar,
                    footer=footer,
                    name=sample_result["title"],
                    figures=[],
                    links=links,
                    desc=link_desc,
                )
                save_html(
                    html_page_path,
                    render_jinja_template(
                        "object.html", self.j_env, args=template_vars
                    ),
                )

        for image_result in image_results:
            html_page_path = os.path.join(
                self.pipeline_reports, f"{image_result}.html".lower()
            )
            figures = []
            for sample in self.prj.samples:
                sample_result = fetch_pipeline_results(
                    project=self.prj,
                    pipeline_name=self.pipeline_name,
                    sample_name=sample.sample_name,
                )
                if image_result not in sample_result:
                    break
                sample_result = sample_result[image_result]
                figures.append(
                    [
                        os.path.relpath(sample_result["path"], self.pipeline_reports),
                        sample.sample_name,
                        os.path.relpath(
                            sample_result["thumbnail_path"], self.pipeline_reports
                        ),
                    ]
                )
            else:
                img_desc = (
                    self.schema[image_result]["description"]
                    if "description" in self.schema[image_result]
                    else "No description in schema"
                )
                template_vars = dict(
                    navbar=navbar,
                    footer=footer,
                    name=sample_result["title"],
                    figures=figures,
                    links=[],
                    desc=img_desc,
                )
                _LOGGER.debug(f"object.html | template_vars:\n{template_vars}")
                save_html(
                    html_page_path,
                    render_jinja_template(
                        "object.html", self.j_env, args=template_vars
                    ),
                )

    def create_sample_html(self, sample_stats, navbar, footer, sample_name):
        """
        Produce an HTML page containing all of a sample's objects
        and the sample summary statistics

        :param str sample_name: the name of the current sample
        :param dict sample_stats: pipeline run statistics for the current sample
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: path to the produced HTML page
        """
        if not os.path.exists(self.pipeline_reports):
            os.makedirs(self.pipeline_reports)
        html_page = os.path.join(self.pipeline_reports, f"{sample_name}.html".lower())

        psms = self.prj.get_pipestat_managers(sample_name=sample_name)
        psm = psms[self.pipeline_name]
        flag = psm.get_status()
        if not flag:
            button_class = "btn btn-secondary"
            flag = "Missing"
        else:
            try:
                flag_dict = BUTTON_APPEARANCE_BY_FLAG[flag]
            except KeyError:
                button_class = "btn btn-secondary"
                flag = "Unknown"
            else:
                button_class = flag_dict["button_class"]
                flag = flag_dict["flag"]
        highlighted_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.pipeline_name,
            sample_name=sample_name,
            inclusion_fun=lambda x: x == "file",
            highlighted=True,
        )

        for k in highlighted_results.keys():
            highlighted_results[k]["path"] = os.path.relpath(
                highlighted_results[k]["path"], self.pipeline_reports
            )

        links = []
        file_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.pipeline_name,
            sample_name=sample_name,
            inclusion_fun=lambda x: x == "file",
        )
        for result_id, result in file_results.items():
            desc = (
                self.schema[result_id]["description"]
                if "description" in self.schema[result_id]
                else ""
            )
            links.append(
                [
                    f"<b>{result['title']}</b>: {desc}",
                    os.path.relpath(result["path"], self.pipeline_reports),
                ]
            )
        image_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.pipeline_name,
            sample_name=sample_name,
            inclusion_fun=lambda x: x == "image",
        )
        figures = []
        for result_id, result in image_results.items():
            figures.append(
                [
                    os.path.relpath(result["path"], self.pipeline_reports),
                    result["title"],
                    os.path.relpath(result["thumbnail_path"], self.pipeline_reports),
                ]
            )

        template_vars = dict(
            report_class="Sample",
            navbar=navbar,
            footer=footer,
            sample_name=sample_name,
            links=links,
            figures=figures,
            button_class=button_class,
            sample_stats=sample_stats,
            flag=flag,
            highlighted_results=highlighted_results,
            pipeline_name=self.pipeline_name,
            amendments=self.prj.amendments,
        )
        _LOGGER.debug(f"sample.html | template_vars:\n{template_vars}")
        save_html(
            html_page, render_jinja_template("sample.html", self.j_env, template_vars)
        )
        return html_page

    def create_status_html(self, status_table, navbar, footer):
        """
        Generates a page listing all the samples, their run status, their
        log file, and the total runtime if completed.

        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: rendered status HTML file
        """
        _LOGGER.debug("Building status page...")
        template_vars = dict(status_table=status_table, navbar=navbar, footer=footer)
        _LOGGER.debug(f"status.html | template_vars:\n{template_vars}")
        return render_jinja_template("status.html", self.j_env, template_vars)

    def create_index_html(self, navbar, footer):
        """
        Generate an index.html style project home page w/ sample summary
        statistics

        :param str navbar: HTML to be included as the navbar in the main
            summary page
        :param str footer: HTML to be included as the footer
        """
        # set default encoding when running in python2
        if sys.version[0] == "2":
            from importlib import reload

            reload(sys)
            sys.setdefaultencoding("utf-8")
        _LOGGER.info(f"Building index page for pipeline: {self.pipeline_name}")

        # Add stats_summary.tsv button link
        stats_file_path = get_file_for_project(
            self.prj, self.pipeline_name, "stats_summary.tsv"
        )
        stats_file_path = (
            os.path.relpath(stats_file_path, self.pipeline_reports)
            if os.path.exists(stats_file_path)
            else None
        )

        # Add objects_summary.yaml button link
        objs_file_path = get_file_for_project(
            self.prj, self.pipeline_name, "objs_summary.yaml"
        )
        objs_file_path = (
            os.path.relpath(objs_file_path, self.pipeline_reports)
            if os.path.exists(objs_file_path)
            else None
        )

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
                casting_fun=str,
            )
            sample_html = self.create_sample_html(
                sample_stat_results, navbar, footer, sample.sample_name
            )
            rel_sample_html = os.path.relpath(sample_html, self.pipeline_reports)
            # treat sample_name column differently - will need to provide
            # a link to the sample page
            table_cell_data = [[rel_sample_html, sample.sample_name]]
            table_cell_data += list(sample_stat_results.values())
            table_row_data.append(table_cell_data)
        # Create parent samples page with links to each sample
        save_html(
            path=os.path.join(self.pipeline_reports, "samples.html"),
            template=self.create_sample_parent_html(navbar, footer),
        )
        _LOGGER.info(" * Creating object pages")
        # Create objects pages
        self.create_object_htmls(navbar, footer)

        # Create parent objects page with links to each object type
        save_html(
            path=os.path.join(self.pipeline_reports, "objects.html"),
            template=self.create_object_parent_html(navbar, footer),
        )
        # Create status page with each sample's status listed
        status_tab = create_status_table(
            pipeline_name=self.pipeline_name,
            project=self.prj,
            pipeline_reports_dir=self.pipeline_reports,
        )
        save_html(
            path=os.path.join(self.pipeline_reports, "status.html"),
            template=self.create_status_html(status_tab, navbar, footer),
        )
        # Complete and close HTML file
        columns = [SAMPLE_NAME_ATTR] + list(sample_stat_results.keys())
        template_vars = dict(
            navbar=navbar,
            stats_file_path=stats_file_path,
            objs_file_path=objs_file_path,
            columns=columns,
            columns_json=dumps(columns),
            table_row_data=table_row_data,
            project_name=self.prj.name,
            pipeline_name=self.pipeline_name,
            stats_json=self._stats_to_json_str(),
            footer=footer,
            amendments=self.prj.amendments,
        )
        _LOGGER.debug(f"index.html | template_vars:\n{template_vars}")
        save_html(
            self.index_html_path,
            render_jinja_template("index.html", self.j_env, template_vars),
        )

    def get_nonhighlighted_results(self, types):
        """
        Get a list of non-highlighted results in the schema

        :param list[str] types: types to narrow down the results
        :return list[str]: result ID that are of the requested type and
            are not highlighted
        """
        results = []
        for k, v in self.schema.items():
            if self.schema[k]["type"] in types:
                if "highlight" not in self.schema[k].keys():
                    results.append(k)
                # intentionally "== False" to exclude "falsy" values
                elif self.schema[k]["highlight"] == False:
                    results.append(k)
        return results

    def _stats_to_json_str(self):
        results = {}
        for sample in self.prj.samples:
            results[sample.sample_name] = fetch_pipeline_results(
                project=self.prj,
                sample_name=sample.sample_name,
                pipeline_name=self.pipeline_name,
                inclusion_fun=lambda x: x not in OBJECT_TYPES,
                casting_fun=str,
            )
        return dumps(results)

    def _get_navbar_dropdown_data_objects(self, objs, wd, context):
        if objs is None or len(objs) == 0:
            return None, None
        relpaths = []
        displayable_ids = []
        for obj_id in objs:
            displayable_ids.append(obj_id.replace("_", " "))
            page_name = os.path.join(
                self.pipeline_reports, (obj_id + ".html").replace(" ", "_").lower()
            )
            relpaths.append(_make_relpath(page_name, wd, context))
        return relpaths, displayable_ids

    def _get_navbar_dropdown_data_samples(self, wd, context):
        relpaths = []
        sample_names = []
        for sample in self.prj.samples:
            page_name = os.path.join(
                self.pipeline_reports,
                f"{sample.sample_name}.html".replace(" ", "_").lower(),
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
        with open(path, "w") as f:
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


def _get_file_for_sample(
    prj, sample_name, appendix, pipeline_name=None, basename=False
):
    """
    Safely looks for files matching the appendix in the specified
    location for the sample

    :param str sample_name: name of the sample that the file name
        should be found for
    :param str appendix: the ending pecific for the file
    :param bool basename: whether to return basename only
    :return str: the name of the matched file
    """
    fp = os.path.join(prj.results_folder, sample_name)
    prepend_name = ""
    if pipeline_name:
        prepend_name += pipeline_name
    if hasattr(prj, AMENDMENTS_KEY) and getattr(prj, AMENDMENTS_KEY):
        prepend_name += f"_{'_'.join(getattr(prj, AMENDMENTS_KEY))}"
    prepend_name = prepend_name + "_" if prepend_name else ""
    fp = os.path.join(fp, f"{prepend_name}{appendix}")
    if os.path.exists(fp):
        return os.path.basename(fp) if basename else fp
    raise FileNotFoundError(fp)


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
    return relpath if not context else os.path.join(os.path.join(*context), relpath)


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
        f"Could not read the log file '{path}' with encodings '{encodings}'"
    )


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


def fetch_pipeline_results(
    project,
    pipeline_name,
    sample_name=None,
    inclusion_fun=None,
    casting_fun=None,
    highlighted=False,
):
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
    :param bool highlighted: return the highlighted or regular results
    :return dict: selected pipeline results
    """
    psms = project.get_pipestat_managers(
        sample_name=sample_name, project_level=sample_name is None
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
    # TODO: can't rely on .data property being there
    rep_data = psm.retrieve()
    # rep_data = psm.data[psm.namespace][psm.record_identifier].items()
    results = {
        k: casting_fun(v)
        for k, v in rep_data.items()
        if k in psm.schema and inclusion_fun(psm.schema[k]["type"])
    }
    if highlighted:
        return {k: v for k, v in results.items() if k in psm.highlighted_results}
    return {k: v for k, v in results.items() if k not in psm.highlighted_results}


def uniqify(seq):
    """Fast way to uniqify while preserving input order."""
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def create_status_table(project, pipeline_name, pipeline_reports_dir):
    """
    Creates status table, the core of the status page.

    :return str: rendered status HTML file
    """

    def _rgb2hex(r, g, b):
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _warn(what, e, sn):
        _LOGGER.warning(
            f"Caught exception: {e}\n"
            f"Could not determine {what} for sample: {sn}. "
            f"Not reported or pipestat status schema is faulty."
        )

    log_paths = []
    log_link_names = []
    sample_paths = []
    sample_names = []
    statuses = []
    status_styles = []
    times = []
    mems = []
    status_descs = []
    for sample in project.samples:
        psms = project.get_pipestat_managers(sample_name=sample.sample_name)
        psm = psms[pipeline_name]
        sample_names.append(sample.sample_name)
        # status and status style
        try:
            status = psm.get_status()
            statuses.append(status)
            status_metadata = psm.status_schema[status]
            status_styles.append(_rgb2hex(*status_metadata["color"]))
            status_descs.append(status_metadata["description"])
        except Exception as e:
            _warn("status", e, sample.sample_name)
            statuses.append(NO_DATA_PLACEHOLDER)
            status_styles.append(NO_DATA_PLACEHOLDER)
            status_descs.append(NO_DATA_PLACEHOLDER)
        sample_paths.append(f"{sample.sample_name}.html".replace(" ", "_").lower())
        # log file path
        try:
            log = psm.retrieve(result_identifier="log")["path"]
            assert os.path.exists(log), FileNotFoundError(f"Not found: {log}")
            log_link_names.append(os.path.basename(log))
            log_paths.append(os.path.relpath(log, pipeline_reports_dir))
        except Exception as e:
            _warn("log", e, sample.sample_name)
            log_link_names.append(NO_DATA_PLACEHOLDER)
            log_paths.append("")
        # runtime and peak mem
        try:
            profile = psm.retrieve(result_identifier="profile")["path"]
            assert os.path.exists(profile), FileNotFoundError(f"Not found: {profile}")
            df = _pd.read_csv(profile, sep="\t", comment="#", names=PROFILE_COLNAMES)
            df["runtime"] = _pd.to_timedelta(df["runtime"])
            times.append(_get_runtime(df))
            mems.append(_get_maxmem(df))
        except Exception as e:
            _warn("profile", e, sample.sample_name)
            times.append(NO_DATA_PLACEHOLDER)
            mems.append(NO_DATA_PLACEHOLDER)

    template_vars = dict(
        sample_names=sample_names,
        log_paths=log_paths,
        status_styles=status_styles,
        statuses=statuses,
        times=times,
        mems=mems,
        sample_paths=sample_paths,
        log_link_names=log_link_names,
        status_descs=status_descs,
    )
    _LOGGER.debug(f"status_table.html | template_vars:\n{template_vars}")
    return render_jinja_template("status_table.html", get_jinja_env(), template_vars)


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
    unique_df = profile_df[~profile_df.duplicated("cid", keep="last").values]
    return str(
        timedelta(seconds=sum(unique_df["runtime"].apply(lambda x: x.total_seconds())))
    ).split(".")[0]
