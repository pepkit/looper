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
        _LOGGER.debug("Reports dir: {}".format(self.reports_dir))

    def __call__(self, objs, stats, columns):
        """ Do the work of the subcommand/program. """
        # Generate HTML report
        navbar = self.create_navbar(self.create_navbar_links(
            objs=objs, stats=stats,
            wd=self._outdir),
            self.index_html_filename)
        navbar_reports = self.create_navbar(
            self.create_navbar_links(
                objs=objs, stats=stats, wd=self.reports_dir),
            os.path.join("..", self.index_html_filename))
        index_html_path = self.create_index_html(
            objs, stats, columns, footer=self.create_footer(),
            navbar=navbar, navbar_reports=navbar_reports)
        return index_html_path

    def create_object_parent_html(self, objs, navbar, footer):
        """
        Generates a page listing all the project objects with links
        to individual object pages

        :param pandas.DataFrame objs: project level dataframe containing any reported objects for all samples
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent objects HTML file
        """
        object_parent_path = os.path.join(self.reports_dir, "objects.html")

        if not os.path.exists(os.path.dirname(object_parent_path)):
            os.makedirs(os.path.dirname(object_parent_path))
        pages = list()
        labels = list()
        if not objs.empty:
            for key in objs['key'].drop_duplicates().sort_values():
                page_name = key + ".html"
                page_path = os.path.join(self.reports_dir, page_name.replace(' ', '_').lower())
                page_relpath = os.path.relpath(page_path, self.reports_dir)
                pages.append(page_relpath)
                labels.append(key)

        template_vars = dict(navbar=navbar, footer=footer, labels=labels, pages=pages, header="Objects")
        return render_jinja_template("navbar_list_parent.html", self.j_env, template_vars)

    def create_sample_parent_html(self, navbar, footer):
        """
        Generates a page listing all the project samples with links
        to individual sample pages
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: Rendered parent samples HTML file
        """
        sample_parent_path = os.path.join(self.reports_dir, "samples.html")

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
                page_path = os.path.join(self.reports_dir, page_name.replace(' ', '_').lower())
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

    def create_navbar_links(self, objs, stats, wd=None, context=None, include_status=True):
        """
        Return a string containing the navbar prebuilt html.

        Generates links to each page relative to the directory of interest (wd arg) or uses the provided context to
        create the paths (context arg)

        :param pandas.DataFrame objs: project results dataframe containing
            object data
        :param list stats[dict] stats: a summary file of pipeline statistics for each
            analyzed sample
        :param path wd: the working directory of the current HTML page being generated, enables navbar links
            relative to page
        :param list[str] context: the context the links will be used in.
            The sequence of directories to be prepended to the HTML file in the resulting navbar
        :param bool include_status: whether the status link should be included in the links set
        :return str: navbar links as HTML-formatted string
        """
        if wd is None and context is None:
            raise ValueError("Either 'wd' (path the links should be relative to) or 'context'"
                             " (the context for the links) has to be provided.")
        status_relpath = _make_relpath(file_name=os.path.join(self.reports_dir, "status.html"), wd=wd, context=context)
        objects_relpath = _make_relpath(file_name=os.path.join(self.reports_dir, "objects.html"), wd=wd, context=context)
        samples_relpath = _make_relpath(file_name=os.path.join(self.reports_dir, "samples.html"), wd=wd, context=context)
        dropdown_keys_objects = None
        dropdown_relpaths_objects = None
        dropdown_relpaths_samples = None
        sample_names = None
        if objs is not None and not objs.dropna().empty:
            # If the number of objects is 20 or less, use a drop-down menu
            if len(objs['key'].drop_duplicates()) <= 20:
                dropdown_relpaths_objects, dropdown_keys_objects = \
                    _get_navbar_dropdown_data_objects(objs=objs, wd=wd, context=context, reports_dir=self.reports_dir)
            else:
                dropdown_relpaths_objects = objects_relpath
        if stats:
            if len(stats) <= 20:
                dropdown_relpaths_samples, sample_names = \
                    _get_navbar_dropdown_data_samples(stats=stats, wd=wd, context=context, reports_dir=self.reports_dir)
            else:
                # Create a menu link to the samples parent page
                dropdown_relpaths_samples = samples_relpath
        status_page_name = "Status" if include_status else None
        template_vars = dict(status_html_page=status_relpath, status_page_name=status_page_name,
                             dropdown_keys_objects=dropdown_keys_objects, objects_page_name="Objects",
                             samples_page_name="Samples", objects_html_page=dropdown_relpaths_objects,
                             samples_html_page=dropdown_relpaths_samples, menu_name_objects="Objects",
                             menu_name_samples="Samples", sample_names=sample_names, all_samples=samples_relpath,
                             all_objects=objects_relpath)
        return render_jinja_template("navbar_links.html", self.j_env, template_vars)

    def create_object_html(self, single_object, navbar, footer):
        """
        Generates a page for an individual object type with all of its
        plots from each sample

        :param pandas.DataFrame single_object: contains reference
            information for an individual object type for all samples
        :param pandas.DataFrame objs: project level dataframe
            containing any reported objects for all samples
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        """

        # Generate object filename
        for key in single_object['key'].drop_duplicates().sort_values():
            # even though it's always one element, loop to extract the data
            current_name = str(key)
            filename = current_name + ".html"
        html_page_path = os.path.join(self.reports_dir, filename.replace(' ', '_').lower())

        if not os.path.exists(os.path.dirname(html_page_path)):
            os.makedirs(os.path.dirname(html_page_path))

        links = []
        figures = []
        warnings = []
        for i, row in single_object.iterrows():
            # Set the PATH to a page for the sample. Catch any errors.
            try:
                object_path = os.path.join(self.prj.results_folder, row['sample_name'], row['filename'])
                object_relpath = os.path.relpath(object_path, self.reports_dir)
            except AttributeError:
                err_msg = ("Sample: {} | " + "Missing valid object path for: {}")
                # Report the sample that fails, if that information exists
                if str(row['sample_name']) and str(row['filename']):
                    _LOGGER.warning(err_msg.format(row['sample_name'], row['filename']))
                else:
                    _LOGGER.warning(err_msg.format("Unknown sample"))
                object_relpath = ""

            # Set the PATH to the image/file. Catch any errors.
            # Check if the object is an HTML document

            if not str(row['anchor_image']).lower().endswith(IMAGE_EXTS):
                image_path = object_path
            else:
                try:
                    image_path = os.path.join(self.prj.results_folder, row['sample_name'], row['anchor_image'])
                except AttributeError:
                    _LOGGER.warning(str(row))
                    err_msg = ("Sample: {} | " + "Missing valid image path for: {}")
                    # Report the sample that fails, if that information exists
                    if str(row['sample_name']) and str(row['filename']):
                        _LOGGER.warning(err_msg.format(row['sample_name'], row['filename']))
                    else:
                        _LOGGER.warning(err_msg.format("Unknown", "Unknown"))
                    image_path = ""
            # Check for the presence of both the file and thumbnail
            if os.path.isfile(image_path) and os.path.isfile(object_path):
                image_relpath = os.path.relpath(image_path, self.reports_dir)
                # If the object has a valid image, use it!
                _LOGGER.debug("Checking image path: {}".format(image_path))
                if str(image_path).lower().endswith(IMAGE_EXTS):
                    figures.append([object_relpath, str(row['sample_name']), image_relpath])
                # Or if that "image" is not an image, treat it as a link
                elif not str(image_path).lower().endswith(IMAGE_EXTS):
                    _LOGGER.debug("Got link")
                    links.append([str(row['sample_name']), image_relpath])
            else:
                warnings.append(str(row['filename']))

        if warnings:
            _LOGGER.warning("create_object_html: " +
                            filename.replace(' ', '_').lower() + " references nonexistent object files")
            _LOGGER.debug(filename.replace(' ', '_').lower() +
                          " nonexistent files: " + ','.join(str(x) for x in warnings))
        template_vars = dict(navbar=navbar, footer=footer, name=current_name, figures=figures, links=links)
        save_html(html_page_path, render_jinja_template("object.html", self.j_env, args=template_vars))

    def create_sample_html(self, objs, sample_name, sample_stats, navbar, footer):
        """
        Produce an HTML page containing all of a sample's objects
        and the sample summary statistics

        :param pandas.DataFrame objs: project level dataframe containing
            any reported objects for all samples
        :param str sample_name: the name of the current sample
        :param dict sample_stats: pipeline run statistics for the current sample
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :return str: path to the produced HTML page
        """
        html_filename = sample_name + ".html"
        html_page = os.path.join(self.reports_dir, html_filename.replace(' ', '_').lower())
        sample_page_relpath = os.path.relpath(html_page, self._outdir)
        single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
        if not os.path.exists(os.path.dirname(html_page)):
            os.makedirs(os.path.dirname(html_page))
        sample_dir = os.path.join(self.prj.results_folder, sample_name)
        if os.path.exists(sample_dir):
            if single_sample.empty:
                # When there is no objects.tsv file, search for the
                # presence of log, profile, and command files
                log_name = _match_file_for_sample(sample_name, 'log.md', self.prj.results_folder)
                profile_name = _match_file_for_sample(sample_name, 'profile.tsv', self.prj.results_folder)
                command_name = _match_file_for_sample(sample_name, 'commands.sh', self.prj.results_folder)
            else:
                log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
            stats_name = "stats.tsv"
            flag = _get_flags(sample_dir)
            # get links to the files
            stats_file_path = _get_relpath_to_file(
                stats_name, sample_name, self.prj.results_folder, self.reports_dir)
            profile_file_path = _get_relpath_to_file(
                profile_name, sample_name, self.prj.results_folder, self.reports_dir)
            commands_file_path = _get_relpath_to_file(
                command_name, sample_name, self.prj.results_folder, self.reports_dir)
            log_file_path = _get_relpath_to_file(
                log_name, sample_name, self.prj.results_folder, self.reports_dir)
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
        figures = []
        warnings = []
        if not single_sample.empty:
            for sample_name in single_sample['sample_name'].drop_duplicates().sort_values():
                o = single_sample[single_sample['sample_name'] == sample_name]
                for i, row in o.iterrows():
                    try:
                        # Image thumbnails are optional
                        # This references to "image" should really
                        # be "thumbnail"
                        image_path = os.path.join(
                            self.prj.results_folder,
                            sample_name, row['anchor_image'])
                        image_relpath = os.path.relpath(image_path, self.reports_dir)
                    except (AttributeError, TypeError):
                        image_path = ""
                        image_relpath = ""

                    # These references to "page" should really be
                    # "object", because they can be anything.
                    page_path = os.path.join(
                        self.prj.results_folder,
                        sample_name, row['filename'])
                    page_relpath = os.path.relpath(page_path, self.reports_dir)
                    # If the object has a thumbnail image, add as a figure
                    if os.path.isfile(image_path) and os.path.isfile(page_path):
                        # If the object has a valid image, add as a figure
                        if str(image_path).lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                            figures.append([page_relpath, str(row['key']), image_relpath])
                        # Otherwise treat as a link
                        elif os.path.isfile(page_path):
                            links.append([str(row['key']), page_relpath])
                        # If neither, there is no object by that name
                        else:
                            warnings.append(str(row['filename']))
                    # If no thumbnail image, it's just a link
                    elif os.path.isfile(page_path):
                        links.append([str(row['key']), page_relpath])
                    # If no file present, there is no object by that name
                    else:
                        warnings.append(str(row['filename']))
        else:
            # Sample was not run through the pipeline
            _LOGGER.warning("{} is not present in {}".format(
                sample_name, self.prj.results_folder))

        template_vars = dict(navbar=navbar, footer=footer, sample_name=sample_name, stats_file_path=stats_file_path,
                             profile_file_path=profile_file_path, commands_file_path=commands_file_path,
                             log_file_path=log_file_path, button_class=button_class, sample_stats=sample_stats,
                             flag=flag, links=links, figures=figures)
        save_html(html_page, render_jinja_template("sample.html", self.j_env, template_vars))
        return sample_page_relpath

    def create_status_html(self, status_table, navbar, footer):
        """
        Generates a page listing all the samples, their run status, their
        log file, and the total runtime if completed.

        :param pandas.DataFrame objs: project level dataframe containing any reported objects for all samples
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

    def create_index_html(self, objs, stats, col_names, navbar, footer, navbar_reports=None):
        """
        Generate an index.html style project home page w/ sample summary
        statistics

        :param pandas.DataFrame objs: project level dataframe containing
            any reported objects for all samples
        :param list[dict] stats: a summary file of pipeline statistics for each
            analyzed sample
        :param list col_names: all unique column names used in the stats file
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :param str navbar_reports: HTML to be included as the navbar for pages in the reports directory
        """
        # set default encoding when running in python2
        if sys.version[0] == '2':
            from importlib import reload
            reload(sys)
            sys.setdefaultencoding("utf-8")
        _LOGGER.debug("Building index page...")
        # copy the columns names and remove the sample_name one, since it will be processed differently
        cols = cp(col_names)
        cols.remove("sample_name")
        if navbar_reports is None:
            navbar_reports = navbar
        if not objs.dropna().empty:
            objs.drop_duplicates(keep='last', inplace=True)
        # Generate parent index.html page path
        index_html_path = get_file_for_project(self.prj, "summary.html")

        # Add stats_summary.tsv button link
        stats_file_name = os.path.join(self._outdir, self.prj.name)
        if hasattr(self.prj, "subproject") and self.prj.subproject:
            stats_file_name += '_' + self.prj.subproject
        stats_file_name += '_stats_summary.tsv'
        stats_file_path = os.path.relpath(stats_file_name, self._outdir)
        # Add stats summary table to index page and produce individual
        # sample pages
        if os.path.isfile(stats_file_name):
            # Produce table rows
            table_row_data = []
            samples_cols_missing = []
            _LOGGER.debug(" * Creating sample pages...")
            for row in stats:
                table_cell_data = []
                sample_name = row["sample_name"]
                sample_page = self.create_sample_html(objs, sample_name, row, navbar_reports, footer)
                # treat sample_name column differently - provide a link to the sample page
                table_cell_data.append([sample_page, sample_name])
                # for each column read the data from the stats
                for c in cols:
                    try:
                        table_cell_data.append(str(row[c]))
                    except KeyError:
                        table_cell_data.append("NA")
                        samples_cols_missing.append(sample_name)
                table_row_data.append(table_cell_data)
            _LOGGER.debug("Samples with missing columns: {}".format(set(samples_cols_missing)))
        else:
            _LOGGER.warning("No stats file '%s'", stats_file_name)

        # Create parent samples page with links to each sample
        save_html(os.path.join(self.reports_dir, "samples.html"), self.create_sample_parent_html(navbar_reports, footer))
        _LOGGER.debug(" * Creating object pages...")
        # Create objects pages
        if not objs.dropna().empty:
            for key in objs['key'].drop_duplicates().sort_values():
                single_object = objs[objs['key'] == key]
                self.create_object_html(single_object, navbar_reports, footer)

        # Create parent objects page with links to each object type
        save_html(os.path.join(self.reports_dir, "objects.html"),
                  self.create_object_parent_html(objs, navbar_reports, footer))
        # Create status page with each sample's status listed
        save_html(os.path.join(self.reports_dir, "status.html"),
                  self.create_status_html(create_status_table(self.prj), navbar_reports, footer))
        # Add project level objects
        project_objects = self.create_project_objects()
        # Complete and close HTML file
        template_vars = dict(project_name=self.prj.name, stats_json=_read_tsv_to_json(stats_file_name),
                             navbar=navbar, footer=footer, stats_file_path=stats_file_path,
                             project_objects=project_objects, columns=col_names, table_row_data=table_row_data)
        save_html(index_html_path, render_jinja_template("index.html", self.j_env, template_vars))
        return index_html_path


def render_jinja_template(name, jinja_env, args=dict()):
    """
    Render template in the specified jinja environment using the provided args

    :param str name: name of the template
    :param dict args: arguments to pass to the template
    :param jinja2.Environment jinja_env: the initialized environment to use in this the looper HTML reports context
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


def _get_flags(sample_dir):
    """
    Get the flag(s) present in the directory

    :param str sample_dir: path to the directory to be searched for flags
    :return list: flags found in the dir
    """
    assert os.path.exists(sample_dir), "The provided path ('{}') does not exist".format(sample_dir)
    flag_files = glob.glob(os.path.join(sample_dir, '*.flag'))
    if len(flag_files) > 1:
        _LOGGER.warning("Multiple flag files ({files_count}) found in sample dir '{sample_dir}'".
                        format(files_count=len(flag_files), sample_dir=sample_dir))
    if len(flag_files) == 0:
        _LOGGER.warning("No flag files found in sample dir '{sample_dir}'".format(sample_dir=sample_dir))
    return [re.search(r'\_([a-z]+)\.flag$', os.path.basename(f)).groups()[0] for f in flag_files]


def _match_file_for_sample(sample_name, appendix, location, full_path=False):
    """
    Safely looks for files matching the appendix in the specified location for the sample

    :param str sample_name: name of the sample that the file name should be found for
    :param str appendix: the ending  specific for the file
    :param str location: where to look for the file
    :param bool full_path: whether to return full path
    :return str: the name of the matched file
    """
    regex = "*" + appendix
    search_pattern = os.path.join(location, sample_name, regex)
    matches = glob.glob(search_pattern)
    if len(matches) < 1:
        return None
    elif len(matches) > 1:
        _LOGGER.warning("matched mutiple files for '{}'. Returning the first one".format(search_pattern))
    return matches[0] if full_path else os.path.basename(matches[0])


def _get_relpath_to_file(file_name, sample_name, location, relative_to):
    """
    Safely gets the relative path for the file for the specified sample

    :param str file_name: name of the file
    :param str sample_name: name of the sample that the file path should be found for
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
    Create a path relative to the context. This function introduces the flexibility to the navbar links creation,
    which the can be used outside of the native looper summary pages.

    :param str file_name: the path to make relative
    :param str wd: the dir the path should be relative to
    :param list[str] context: the context the links will be used in.
            The sequence of directories to be prepended to the HTML file in the resulting navbar
    :return str: relative path
    """
    relpath = os.path.relpath(file_name, wd)
    return relpath if not context else os.path.join(os.path.join(*context), relpath)


def _get_navbar_dropdown_data_objects(objs, wd, context, reports_dir):
    if objs is None:
        return None, None
    relpaths = []
    df_keys = objs['key'].drop_duplicates().sort_values()
    for key in df_keys:
        page_name = os.path.join(reports_dir, (key + ".html").replace(' ', '_').lower())
        relpaths.append(_make_relpath(page_name, wd, context))
    return relpaths, df_keys


def _get_navbar_dropdown_data_samples(stats, wd, context, reports_dir):
    if stats is None:
        return None, None
    relpaths = []
    sample_names = []
    for sample in stats:
        for entry, val in sample.items():
            if entry == "sample_name":
                sample_name = str(val)
                page_name = os.path.join(reports_dir, (sample_name + ".html").replace(' ', '_').lower())
                relpaths.append(_make_relpath(page_name, wd, context))
                sample_names.append(sample_name)
                break
            else:
                _LOGGER.warning("Could not determine sample name in stats.tsv")
    return relpaths, sample_names


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
    _LOGGER.warning("Could not read the log file '{p}' with encodings '{enc}'".format(p=path, enc=encodings))


def _get_from_log(log_path, regex):
    """
    Get the value for the matched key from log file

    :param str log_path: path to the log file
    :param str regex: matching str. Should be formatted as follows: r'(phrase to match)'
    :return str: matched and striped string
    :raises IOError: when the file is not found in the provided path
    """
    if not os.path.exists(log_path):
        raise IOError("Can't read the log file '{}'. Not found".format(log_path))
    log = _read_csv_encodings(log_path, header=None, names=['data'])
    if log is None:
        _LOGGER.warning("'{r}' was not read from log".format(r=regex))
        return None
    # match regex, get row(s) that matched the regex
    log_row = log.iloc[:, 0].str.extractall(regex)
    # not matches? return None
    if log_row.empty:
        return None
    if log_row.size > 1:
        _LOGGER.warning("When parsing '{lp}', more than one values matched with: {r}. Returning first.".format(lp=log_path, r=regex))
    # split the matched line by first colon return stripped data.
    # This way both mem values (e.g 1.1GB) and time values (e.g 1:10:10) will work.
    val = log.iloc[log_row.index[0][0]].str.split(":", 1, expand=True)[1][0].strip()
    return val


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


def uniqify(seq):
    """ Fast way to uniqify while preserving input order. """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def create_status_table(prj, final=True):
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
            flag = _get_flags(sample_dir)
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
            page_path = os.path.join(get_file_for_project(prj, "reports"),
                                     page_name.replace(' ', '_').lower())
            page_relpath = os.path.relpath(page_path,
                                           get_file_for_project(prj, "reports"))
            sample_paths.append(page_relpath)
            sample_link_names.append(sample_name)
            # get second column data (status/flag)
            flags.append(flag)
            # get third column data (log file/link)
            log_name = _match_file_for_sample(sample_name, "log.md",
                                              prj.results_folder)
            log_file_link = \
                _get_relpath_to_file(log_name, sample_name, prj.results_folder,
                                     get_file_for_project(prj, "reports"))
            log_link_names.append(log_name)
            log_paths.append(log_file_link)
            # get fourth column data (runtime) and fifth column data (memory)
            profile_file_path = \
                _match_file_for_sample(sample.sample_name, 'profile.tsv',
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


def _get_maxmem(profile_df):
    """
    Get current peak memory

    :param pandas.core.frame.DataFrame profile_df: a data frame representing the current profile.tsv for a sample
    :return str: max memory
    """
    return "{} GB".format(str(max(profile_df['mem']) if not profile_df['mem'].empty else 0))


def _get_runtime(profile_df):
    """
    Collect the unique and last duplicated runtimes, sum them and then return in str format

    :param pandas.core.frame.DataFrame profile_df: a data frame representing the current profile.tsv for a sample
    :return str: sum of runtimes
    """
    unique_df = profile_df[~profile_df.duplicated('cid', keep='last').values]
    return str(timedelta(seconds=sum(unique_df['runtime'].apply(lambda x: x.total_seconds())))).split(".")[0]

