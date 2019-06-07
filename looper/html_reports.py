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
from .const import TEMPLATES_DIRNAME, APPEARANCE_BY_FLAG, NO_DATA_PLACEHOLDER, IMAGE_EXTS, PROFILE_COLNAMES
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
        self.reports_dir = get_reports_dir(self.prj)
        self.index_html_path = get_index_html_path(self.prj)
        _LOGGER.debug("Reports dir: {}".format(self.reports_dir))

    def __call__(self, objs, stats, columns):
        """ Do the work of the subcommand/program. """

        # Generate HTML report
        index_html_path = self.create_index_html(objs, stats, columns,
                                                 navbar=self.create_navbar(self.create_navbar_links(
                                                     prj=self.prj, objs=objs, stats=stats,
                                                     wd=self.prj.metadata.output_dir)),
                                                 footer=self.create_footer())
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

    def create_navbar(self, navbar_links):
        """
        Creates the navbar using the privided links

        :param str navbar_links: HTML list of links to be inserted into a navbar
        :return str: navbar HTML
        """
        template_vars = dict(navbar_links=navbar_links, index_html=self.index_html_path)
        return render_jinja_template("navbar.html", self.j_env, template_vars)

    def create_footer(self):
        """
        Renders the footer from the templates directory

        :return str: footer HTML
        """
        return render_jinja_template("footer.html", self.j_env, dict(version=v))

    def create_navbar_links(self, prj, objs, stats, wd=None, context=None):
        """
        Return a string containing the navbar prebuilt html.

        Generates links to each page relative to the directory of interest (wd arg) or uses the provided context to
        create the paths (context arg)

        :param looper.Project prj: a project the navbar links should be created for
        :param pandas.DataFrame objs: project results dataframe containing
            object data
        :param list stats[dict] stats: a summary file of pipeline statistics for each
            analyzed sample
        :param path wd: the working directory of the current HTML page
            being generated, enables navbar links relative to page
        :param list[str] context: the context the links will be used in
        """
        if wd is None and context is None:
            raise ValueError("Either 'wd' (path the links should be relative to) or 'context'"
                             " (the context for the links) has to be provided.")
        status_relpath = _make_relpath(prj=prj, file_name="status.html", dir=wd, context=context)
        objects_relpath = _make_relpath(prj=prj, file_name="objects.html", dir=wd, context=context)
        samples_relpath = _make_relpath(prj=prj, file_name="samples.html", dir=wd, context=context)
        dropdown_keys_objects = None
        dropdown_relpaths_objects = None
        dropdown_relpaths_samples = None
        sample_names = None
        if objs is not None and not objs.dropna().empty:
            # If the number of objects is 20 or less, use a drop-down menu
            if len(objs['key'].drop_duplicates()) <= 20:
                dropdown_relpaths_objects, dropdown_keys_objects = \
                    _get_navbar_dropdown_data_objects(prj=prj, objs=objs, wd=wd, context=context)
            else:
                dropdown_relpaths_objects = objects_relpath
        if stats:
            if len(stats) <= 20:
                dropdown_relpaths_samples, sample_names = \
                    _get_navbar_dropdown_data_samples(prj=prj, stats=stats, wd=wd, context=context)
            else:
                # Create a menu link to the samples parent page
                dropdown_relpaths_samples = samples_relpath
        template_vars = dict(status_html_page=status_relpath, status_page_name="Status",
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
        object_path = os.path.join(self.reports_dir, filename.replace(' ', '_').lower())

        if not os.path.exists(os.path.dirname(object_path)):
            os.makedirs(os.path.dirname(object_path))

        links = []
        figures = []
        warnings = []
        for i, row in single_object.iterrows():
            # Set the PATH to a page for the sample. Catch any errors.
            try:
                page_path = os.path.join(self.prj.results_folder, row['sample_name'], row['filename'])
            except AttributeError:
                err_msg = ("Sample: {} | " + "Missing valid page path for: {}")
                # Report the sample that fails, if that information exists
                if str(row['sample_name']) and str(row['filename']):
                    _LOGGER.warn(err_msg.format(row['sample_name'], row['filename']))
                else:
                    _LOGGER.warn(err_msg.format("Unknown sample"))
                page_path = ""
            if not page_path.strip():
                page_relpath = os.path.relpath(page_path, self.reports_dir)
            else:
                page_relpath = ""

            # Set the PATH to the image/file. Catch any errors.
            # Check if the object is an HTML document
            if not str(row['filename']).lower().endswith(IMAGE_EXTS):
                image_path = page_path
            else:
                try:
                    image_path = os.path.join(self.prj.results_folder,
                                              row['sample_name'], row['anchor_image'])
                except AttributeError:
                    _LOGGER.warn(str(row))
                    err_msg = ("Sample: {} | " + "Missing valid image path for: {}")
                    # Report the sample that fails, if that information exists
                    if str(row['sample_name']) and str(row['filename']):
                        _LOGGER.warn(err_msg.format(row['sample_name'], row['filename']))
                    else:
                        _LOGGER.warn(err_msg.format("Unknown", "Unknown"))
                    image_path = ""

            # Check for the presence of both the file and thumbnail
            if os.path.isfile(image_path) and os.path.isfile(page_path):
                image_relpath = os.path.relpath(image_path, self.reports_dir)
                # If the object has a valid image, use it!
                if str(image_path).lower().endswith(IMAGE_EXTS):
                    figures.append([page_relpath, str(row['sample_name']), image_relpath])
                # Or if that "image" is not an image, treat it as a link
                elif not str(image_path).lower().endswith(IMAGE_EXTS):
                    links.append([str(row['sample_name']), image_relpath])
            else:
                warnings.append(str(row['filename']))

        if warnings:
            _LOGGER.warning("create_object_html: " +
                            filename.replace(' ', '_').lower() + " references nonexistent object files")
            _LOGGER.debug(filename.replace(' ', '_').lower() +
                          " nonexistent files: " + ','.join(str(x) for x in warnings))
        template_vars = dict(navbar=navbar, footer=footer, name=current_name, figures=figures, links=links)
        save_html(object_path, render_jinja_template("object.html", self.j_env, args=template_vars))

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
        sample_page_relpath = os.path.relpath(html_page, self.prj.metadata.output_dir)
        single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
        if not os.path.exists(os.path.dirname(html_page)):
            os.makedirs(os.path.dirname(html_page))
        sample_dir = os.path.join(self.prj.results_folder, sample_name)
        button_appearance_by_flag = {
            "completed": {
                "button_class": "btn btn-success",
                "flag": "Completed"
            },
            "running": {
                "button_class": "btn btn-warning",
                "flag": "Running"
            },
            "failed": {
                "button_class": "btn btn-danger",
                "flag": "Failed"
            }
        }
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
                button_class = "btn btn-danger"
                flag = "Missing"
            elif len(flag) > 1:
                button_class = "btn btn-warning"
                flag = "Multiple"
            else:
                flag = flag[0]
                try:
                    flag_dict = button_appearance_by_flag[flag]
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
        template_vars = dict(status_table=status_table, navbar=navbar, footer=footer)
        return render_jinja_template("status.html", self.j_env, template_vars)

    def create_project_objects(self):
        """ Render available project level summaries as additional figures/links """
        _LOGGER.debug("Building project object...")
        all_protocols = [sample.protocol for sample in self.prj.samples]

        # For each protocol report the project summarizers' results
        for protocol in set(all_protocols):
            figures = []
            links = []
            warnings = []
            ifaces = self.prj.get_interfaces(protocol)

            # Check the interface files for summarizers
            for iface in ifaces:
                pl = iface.fetch_pipelines(protocol)
                summary_results = iface.get_attribute(pl, "summary_results")

                # Build the HTML for each summary result
                if summary_results is not None:
                    for result in summary_results:
                        caption = str(result['caption'])
                        result_file = str(result['path']).replace('{name}', str(self.prj.name))
                        result_img = str(result['thumbnail_path']).replace('{name}', str(self.prj.name))
                        search = os.path.join(self.prj.metadata.output_dir, '{}'.format(result_file))

                        # Confirm the file itself was produced
                        if glob.glob(search):
                            file_path = str(glob.glob(search)[0])
                            file_relpath = os.path.relpath(file_path, self.prj.metadata.output_dir)
                            search = os.path.join(self.prj.metadata.output_dir, '{}'.format(result_img))

                            # Add as a figure if thumbnail exists
                            if glob.glob(search):
                                img_path = str(glob.glob(search)[0])
                                img_relpath = os.path.relpath(img_path, self.prj.metadata.output_dir)
                                figures.append([file_relpath, '{}: Click to see full-size figure'.format(caption),
                                                img_relpath])
                            # add as a link otherwise
                            else:
                                links.append(['{}: Click to see full-size figure'.format(caption), file_relpath])

                        else:
                            warnings.append(caption)
                else:
                    _LOGGER.debug("No custom summarizers were found for this pipeline. Proceeded with default only.")
            if warnings:
                _LOGGER.warning("Summarizer was unable to find: " + ', '.join(str(x) for x in warnings))

        template_vars = dict(figures=figures, links=links)
        return render_jinja_template("project_object.html", self.j_env, template_vars)

    def create_index_html(self, objs, stats, col_names, navbar, footer, navbar_reports=None):
        """
        Generate an index.html style project home page w/ sample summary
        statistics

        :param pandas.DataFrame objs: project level dataframe containing
            any reported objects for all samples
        :param list stats[dict]: a summary file of pipeline statistics for each
            analyzed sample
        :param list col_names: all unique column names used in the stats file
        :param str navbar: HTML to be included as the navbar in the main summary page
        :param str footer: HTML to be included as the footer
        :param str navbar_reports: HTML to be included as the navbar for pages in the reports directory
        """
        # set default encoding when running in python2
        if sys.version[0] == '2':
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
        index_html_path = get_index_html_path(self.prj)

        # Add stats_summary.tsv button link
        stats_file_name = os.path.join(self.prj.metadata.output_dir, self.prj.name)
        if hasattr(self.prj, "subproject") and self.prj.subproject:
            stats_file_name += '_' + self.prj.subproject
        stats_file_name += '_stats_summary.tsv'
        stats_file_path = os.path.relpath(stats_file_name, self.prj.metadata.output_dir)
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


def get_reports_dir(prj):
    """
    Get the reports directory path depending on the subproject activation status

    :param looper.Project prj: the project to determine the reports directory for
    :return str: path to the reports directory
    """
    rep_dir_name = "reports" if prj.subproject is None else "reports_" + prj.subproject
    return os.path.join(prj.metadata.output_dir, rep_dir_name)


def get_index_html_path(prj):
    """
    Get the index HTML path depending on the subproject activation status

    :param looper.Project prj: the project to determine the index HTML path for
    :return str: path to the index HTML
    """
    index_html_root = os.path.join(prj.metadata.output_dir, prj.name)
    if prj.subproject is not None:
        index_html_root += "_" + prj.subproject
    return index_html_root + "_summary.html"


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


def _make_relpath(prj, file_name, dir, context):
    """
    Create a path relative to the context. This function introduces the flexibility to the navbar links creation,
    which the can be used outside of the native looper summary pages.

    :param str path: the path to make relative
    :param str dir: the dir the path should be relative to
    :param list[str] context: names of the directories that create the context for the path
    :return str: relative path
    """
    rep_dir = os.path.basename(get_reports_dir(prj))
    if context is not None:
        full_context = ["summary", rep_dir]
        caravel_mount_point = [item for item in full_context if item not in context]
        caravel_mount_point.append(file_name)
        relpath = os.path.join(*caravel_mount_point)
    else:
        relpath = os.path.relpath(file_name, dir)
    return relpath


def _get_navbar_dropdown_data_objects(prj, objs, wd, context):
    if objs is None:
        return None, None
    rep_dir_path = get_reports_dir(prj)
    rep_dir = os.path.basename(rep_dir_path)
    relpaths = []
    df_keys = objs['key'].drop_duplicates().sort_values()
    for key in df_keys:
        page_name = (key + ".html").replace(' ', '_').lower()
        page_path = os.path.join(rep_dir_path, page_name)
        if context is not None:
            full_context = ["summary", rep_dir]
            caravel_mount_point = [item for item in full_context if item not in context]
            caravel_mount_point.append(page_name)
            relpath = os.path.join(*caravel_mount_point)
        else:
            relpath = os.path.relpath(page_path, wd)
        relpaths.append(relpath)
    return relpaths, df_keys


def _get_navbar_dropdown_data_samples(prj, stats, wd, context):
    if stats is None:
        return None, None
    rep_dir_path = get_reports_dir(prj)
    rep_dir = os.path.basename(rep_dir_path)
    relpaths = []
    sample_names = []
    for sample in stats:
        for entry, val in sample.items():
            if entry == "sample_name":
                sample_name = str(val)
                page_name = (sample_name + ".html").replace(' ', '_').lower()
                page_path = os.path.join(rep_dir_path, page_name)
                if context is not None:
                    full_context = ["summary", rep_dir]
                    caravel_mount_point = [item for item in full_context if item not in context]
                    caravel_mount_point.append(page_name)
                    relpath = os.path.join(*caravel_mount_point)
                else:
                    relpath = os.path.relpath(page_path, wd)
                relpaths.append(relpath)
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
    It is abstracted into a function so that it can be used in other software packages.
    It can produce a table of two types. With links to the samples/log files and without.
    The one without can be used to render HTMLs for on-th-fly job status inspection

    :param looper.Project prj: project to create the status table for
    :param bool final: if the status table is created for a finalized looper run. In such a case,
    links to samples and log files will be provided
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
                    flag_dict = APPEARANCE_BY_FLAG[flag]
                except KeyError:
                    button_class = "table-secondary"
                    flag = "Unknown"
                else:
                    button_class = flag_dict["button_class"]
                    flag = flag_dict["flag"]
            row_classes.append(button_class)
            # get first column data (sample name/link)
            page_name = sample_name + ".html"
            page_path = os.path.join(get_reports_dir(prj), page_name.replace(' ', '_').lower())
            page_relpath = os.path.relpath(page_path, get_reports_dir(prj))
            sample_paths.append(page_relpath)
            sample_link_names.append(sample_name)
            # get second column data (status/flag)
            flags.append(flag)
            # get third column data (log file/link)
            log_name = _match_file_for_sample(sample_name, "log.md", prj.results_folder)
            log_file_link = _get_relpath_to_file(log_name, sample_name, prj.results_folder,
                                                 get_reports_dir(prj))
            log_link_names.append(log_name)
            log_paths.append(log_file_link)
            # get fourth column data (runtime) and fifth column data (memory)
            profile_file_path = _match_file_for_sample(sample.sample_name, 'profile.tsv', prj.results_folder,
                                                       full_path=True)
            if os.path.exists(profile_file_path):
                df = _pd.read_csv(profile_file_path, sep="\t", comment="#", names=PROFILE_COLNAMES)
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
        warn("The stats table is incomplete, likely because " +
             "one or more jobs either failed or is still running.")
    if sample_warning:
        if len(sample_warning) == 1:
            warn("{} is not present in {}".format(
                ''.join(str(sample) for sample in sample_warning),
                prj.results_folder))
        else:
            warn_msg = "The following samples are not present in {}: {}"
            warn(warn_msg.format(
                prj.results_folder,
                ' '.join(str(sample) for sample in sample_warning)))
    template_vars = dict(sample_link_names=sample_link_names, row_classes=row_classes, flags=flags, times=times,
                         mems=mems)
    template_name = "status_table_no_links.html"
    if final:
        template_name = "status_table.html"
        template_vars.update(dict(sample_paths=sample_paths, log_link_names=log_link_names, log_paths=log_paths))
    return render_jinja_template(template_name, get_jinja_env(), template_vars)


def _get_maxmem(profile_df):
    """
    Get current peak memory

    :param pandas.core.frame.DataFrame profile_df: a data frame representing the current profile.tsv for a sample
    :return str: max memory
    """
    return "{} GB".format(str(max(profile_df['mem'])))


def _get_runtime(profile_df):
    """
    Collect the unique and last duplicated runtimes, sum them and then return in str format

    :param pandas.core.frame.DataFrame profile_df: a data frame representing the current profile.tsv for a sample
    :return str: sum of runtimes
    """
    unique_df = profile_df[~profile_df.duplicated('cid', keep='last').values]
    return str(timedelta(seconds=sum(unique_df['runtime'].apply(lambda x: x.total_seconds())))).split(".")[0]

