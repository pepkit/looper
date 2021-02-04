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
from .pipeline_interface import PipelineInterface
from .exceptions import PipelineInterfaceConfigError
from .html_reports import HTMLReportBuilder, render_jinja_template, \
    get_jinja_env, save_html, fetch_pipeline_results, \
    _get_file_for_sample, _get_flags
from .processed_project import get_project_outputs
from .utils import get_file_for_project
from peppy.const import *
from eido import read_schema
from copy import copy as cp
_LOGGER = logging.getLogger("looper")


class HTMLReportBuilderProject(object):
    """ Generate HTML summary report for project/samples """

    def __init__(self, prj):
        """
        The Project defines the instance.

        :param looper.Project prj: Project with which to work/operate on
        :param bool project_level: whether to generate a project-level
            pipeline report
        """
        super(HTMLReportBuilderProject, self).__init__()
        self.prj = prj
        self.j_env = get_jinja_env()
        self.output_dir = self.prj.output_dir
        self.reports_dir = os.path.join(self.output_dir, "reports")
        _LOGGER.debug(f"Reports dir: {self.reports_dir}")

    def __call__(self, piface_source):
        """
        Generate HTML report.

        :param str piface_source: path to the pipeline interface defining
            connection to the pipeline to generate the report for
        :return str: path to the index page of the generated HTML report
        """
        # Generate HTML report
        self.prj_piface_source = piface_source
        self.prj_piface = PipelineInterface(config=self.prj_piface_source)
        self.amendments_str = "_".join(self.prj.amendments) \
            if self.prj.amendments else ""
        self.pipeline_reports = os.path.join(
            self.reports_dir,
            f"{self.prj_piface.pipeline_name}_{self.amendments_str}"
            if self.prj.amendments else self.prj_piface.pipeline_name
        )
        pifaces = self.prj.project_pipeline_interfaces
        selected_pipeline_pifaces = \
            [p for p in pifaces if p.pipeline_name == self.prj_piface.pipeline_name]
        schema_path = self.prj.get_schemas(
            selected_pipeline_pifaces, OUTPUT_SCHEMA_KEY)[0]
        self.schema = read_schema(schema_path)[0]
        self.index_html_path = os.path.join(
            self.pipeline_reports, f"{self.prj.name}.html")
        linked_sample_reports = {}
        html_report_builder = HTMLReportBuilder(prj=self.prj)
        for sample_piface_source in \
                self.prj.linked_sample_interfaces[self.prj_piface_source]:
            # Do the stats and object summarization.
            pipeline_name = PipelineInterface(sample_piface_source).pipeline_name
            # run the report builder. a set of HTML pages is produced
            report_path = html_report_builder(
                pipeline_name=pipeline_name,
                project_index_html=self.index_html_path
            )
            if pipeline_name in linked_sample_reports:
                raise PipelineInterfaceConfigError(
                    f"Duplicate pipeline_names found in pipeline interfaces "
                    f"defined for samples in this project: {pipeline_name}")
            linked_sample_reports[pipeline_name] = report_path
            _LOGGER.info(
                f"Sample-level '{pipeline_name}' pipeline HTML report: "
                f"{report_path}")

        sample_reps_parent = os.path.join(
            self.pipeline_reports, "sample_reports.html")
        sample_reports_parent_relpath = os.path.relpath(
            sample_reps_parent, self.pipeline_reports)
        navbar = self.create_navbar(
            navbar_links=self.create_navbar_links(
                sample_reports_parent_relpath=sample_reports_parent_relpath
            ),
            index_html_relpath=os.path.basename(self.index_html_path)
        )
        save_html(
            path=sample_reps_parent,
            template=self.create_sample_reports_parent(
                linked_sample_reports=linked_sample_reports,
                navbar=navbar,
                footer=self.create_footer()
            )
        )
        self.create_index_html(navbar=navbar, footer=self.create_footer())
        return self.index_html_path

    def create_navbar_links(self, sample_reports_parent_relpath):
        template_vars = dict(
            status_html_page=None, dropdown_keys_objects=None, objects_html_page=None,
            samples_html_page=None, sample_names=None, all_samples=None,
            all_objects=None, sample_reports_parent=sample_reports_parent_relpath,
            project_report=None
        )
        _LOGGER.debug(f"navbar_links.html | template_vars:\n{template_vars}")
        return render_jinja_template("navbar_links.html", self.j_env, template_vars)

    def create_sample_reports_parent(self, linked_sample_reports, navbar, footer):

        template_vars = dict(
            navbar=navbar, footer=footer, header="Linked sample pipelines",
            labels=list(linked_sample_reports.keys()),
            pages=list(linked_sample_reports.values())
        )
        _LOGGER.debug(f"navbar_list_parent.html | template_vars: \n{template_vars}")
        return render_jinja_template(
            "navbar_list_parent.html", self.j_env, template_vars)

    def create_footer(self):
        """
        Renders the footer from the templates directory

        :return str: footer HTML
        """
        return render_jinja_template("footer.html", self.j_env, dict(version=v))

    def create_navbar(self, navbar_links, index_html_relpath):
        """
        Creates the navbar using the provided links

        :param str navbar_links: HTML list of links to be inserted into a navbar
        :return str: navbar HTML
        """
        template_vars = dict(
            navbar_links=navbar_links, index_html=index_html_relpath
        )
        return render_jinja_template("navbar.html", self.j_env, template_vars)

    def create_index_html(self, navbar, footer):
        project_stat_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.prj_piface.pipeline_name,
            inclusion_fun=lambda x: x not in OBJECT_TYPES,
            casting_fun=str
        )
        return self.create_sample_html(
            project_stat_results, navbar, footer)

    def create_sample_html(self, sample_stats, navbar, footer):
        """
        Produce an HTML page containing all of a sample's objects
        and the sample summary statistics

        :param dict sample_stats: pipeline run statistics for the current sample
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: path to the produced HTML page
        """
        if not os.path.exists(self.pipeline_reports):
            os.makedirs(self.pipeline_reports)

        sample_name = self.prj.name
        html_page = os.path.join(
            self.pipeline_reports, f"{sample_name}.html".lower())

        sample_dir = os.path.join(self.prj.results_folder, sample_name)
        if os.path.exists(sample_dir):
            log_path = _get_file_for_sample(
                self.prj, sample_name, "log.md", self.prj_piface.pipeline_name)
            profile_path = _get_file_for_sample(
                self.prj, sample_name, "profile.tsv", self.prj_piface.pipeline_name)
            commands_path = _get_file_for_sample(
                self.prj, sample_name, "commands.sh", self.prj_piface.pipeline_name)
            stats_path = _get_file_for_sample(
                self.prj, sample_name, "stats.tsv")
            # get links to the files
            stats_file_path = os.path.relpath(stats_path, self.pipeline_reports)
            profile_file_path = os.path.relpath(profile_path, self.pipeline_reports)
            commands_file_path = os.path.relpath(commands_path, self.pipeline_reports)
            log_file_path = os.path.relpath(log_path, self.pipeline_reports)
            flag = _get_flags(sample_dir, self.prj_piface.pipeline_name)
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
            pipeline_name=self.prj_piface.pipeline_name,
            sample_name=None,
            inclusion_fun=lambda x: x == "file"
        )
        for result_id, result in file_results.items():
            desc = self.schema[result_id]["description"] \
                if "description" in self.schema[result_id] else ""
            links.append([f"<b>{result['title']}</b>: {desc}", result["path"]])
        image_results = fetch_pipeline_results(
            project=self.prj,
            pipeline_name=self.prj_piface.pipeline_name,
            sample_name=None,
            inclusion_fun=lambda x: x == "image"
        )
        figures = []
        for result_id, result in image_results.items():
            figures.append(
                [result["path"], result["title"], result["thumbnail_path"]])

        template_vars = dict(
            report_class="Project",
            navbar=navbar, footer=footer, sample_name=sample_name,
            stats_file_path=stats_file_path, links=links,
            profile_file_path=profile_file_path,  figures=figures,
            commands_file_path=commands_file_path, log_file_path=log_file_path,
            button_class=button_class, sample_stats=sample_stats, flag=flag,
            pipeline_name=self.prj_piface.pipeline_name, amendments=self.prj.amendments
        )
        _LOGGER.debug(f"sample.html | template_vars:\n{template_vars}")
        save_html(html_page, render_jinja_template(
            "sample.html", self.j_env, template_vars))
        return html_page