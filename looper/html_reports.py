""" Generate HTML reports """

import os
import glob
import pandas as _pd
import logging
import jinja2
import re

from _version import __version__ as v
from collections import OrderedDict

TEMPLATES_DIRNAME = "jinja_templates"
_LOGGER = logging.getLogger('HTMLReportBuilder')


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
        self.reports_dir = self.get_reports_dir()
        _LOGGER.debug("Reports dir: {}".format(self.reports_dir))

    def __call__(self, objs, stats, columns):
        """ Do the work of the subcommand/program. """

        def get_index_html_path():
            """
            Get the index HTML path depending on the subproject activation status

            :return str: path to the index HTML
            """
            index_html_root = os.path.join(self.prj.metadata.output_dir, self.prj.name)
            if self.prj.subproject is not None:
                index_html_root += "_" + self.prj.subproject
            return index_html_root + "_summary.html"

        def create_object_parent_html(objs, stats, wd):
            """
            Generates a page listing all the project objects with links
            to individual object pages

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
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

            template_vars = dict(navbar=create_navbar(create_navbar_links(objs, stats, wd)), labels=labels, pages=pages, header="Objects",
                                 version=v)
            return self.render_jinja_template("navbar_list_parent.html", template_vars)

        def create_sample_parent_html(objs, stats, wd):
            """
            Generates a page listing all the project samples with links
            to individual sample pages
            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
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
                        self.prj.metadata.results_subdir, sample_name)

                # Confirm sample directory exists, then build page
                if os.path.exists(sample_dir):
                    page_name = sample_name + ".html"
                    page_path = os.path.join(self.reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, self.reports_dir)
                    pages.append(page_relpath)
                    labels.append(sample_name)

            template_vars = dict(navbar=create_navbar(create_navbar_links(objs, stats, wd)), labels=labels, pages=pages, header="Samples",
                                 version=v)
            return self.render_jinja_template("navbar_list_parent.html", template_vars)

        def create_object_html(single_object, objs, stats, wd):
            """
            Generates a page for an individual object type with all of its
            plots from each sample

            :param panda.DataFrame single_object: contains reference
                information for an individual object type for all samples
            :param panda.DataFrame objs: project level dataframe
                containing any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
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
                    page_path = os.path.join(self.prj.metadata.results_subdir, row['sample_name'], row['filename'])
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
                if str(row['filename']).lower().endswith(".html"):
                    image_path = page_path
                else:
                    try:
                        image_path = os.path.join(self.prj.metadata.results_subdir,
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
                    if str(image_path).lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                        figures.append([page_relpath, str(row['sample_name']), image_relpath])
                    # Or if that "image" is an HTML document
                    elif str(image_path).lower().endswith('.html'):
                        links.append([str(row['sample_name']), image_relpath])
                    # Otherwise treat as a link
                    elif os.path.isfile(page_path):
                        links.append([str(row['sample_name']), page_relpath])
                    else:
                        warnings.append(str(row['filename']))
                # If no thumbnail image is present, add as a link
                elif os.path.isfile(page_path):
                    links.append([str(row['sample_name']), page_relpath])
                else:
                    warnings.append(str(row['filename']))

            if warnings:
                _LOGGER.warning("create_object_html: " +
                                filename.replace(' ', '_').lower() + " references nonexistent object files")
                _LOGGER.debug(filename.replace(' ', '_').lower() +
                              " nonexistent files: " + ','.join(str(x) for x in warnings))
            template_vars = dict(navbar=create_navbar(create_navbar_links(objs, stats, wd)), name=current_name, figures=figures, links=links,
                                 version=v)
            save_html(object_path, self.render_jinja_template("object.html", args=template_vars))

        def create_sample_html(objs, stats, sample_name, sample_stats, wd):
            """
            Produce an HTML page containing all of a sample's objects
            and the sample summary statistics

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str sample_name: the name of the current sample
            :param list stats: pipeline run statistics for the current sample
            :param str wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
            :return str: path to the produced HTML page
            """
            html_filename = sample_name + ".html"
            html_page = os.path.join(self.reports_dir, html_filename.replace(' ', '_').lower())
            sample_page_relpath = os.path.relpath(html_page, self.prj.metadata.output_dir)
            single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
            if not os.path.exists(os.path.dirname(html_page)):
                os.makedirs(os.path.dirname(html_page))
            sample_dir = os.path.join(self.prj.metadata.results_subdir, sample_name)
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
                    log_name = _match_file_for_sample(sample_name, 'log.md', self.prj.metadata.results_subdir)
                    profile_name = _match_file_for_sample(sample_name, 'profile.tsv', self.prj.metadata.results_subdir)
                    command_name = _match_file_for_sample(sample_name, 'commands.sh', self.prj.metadata.results_subdir)
                else:
                    log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                    profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                    command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
                stats_name = "stats.tsv"
                flag = _get_flags(sample_dir)
                # get links to the files
                stats_file_path = _get_relpath_to_file(
                    stats_name, sample_name, self.prj.metadata.results_subdir, self.reports_dir)
                profile_file_path = _get_relpath_to_file(
                    profile_name, sample_name, self.prj.metadata.results_subdir, self.reports_dir)
                commands_file_path = _get_relpath_to_file(
                    command_name, sample_name, self.prj.metadata.results_subdir, self.reports_dir)
                log_file_path = _get_relpath_to_file(
                    log_name, sample_name, self.prj.metadata.results_subdir, self.reports_dir)
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
                                self.prj.metadata.results_subdir,
                                sample_name, row['anchor_image'])
                            image_relpath = os.path.relpath(image_path, self.reports_dir)
                        except AttributeError:
                            image_path = ""
                            image_relpath = ""

                        # These references to "page" should really be
                        # "object", because they can be anything.
                        page_path = os.path.join(
                            self.prj.metadata.results_subdir,
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
                    sample_name, self.prj.metadata.results_subdir))

            template_vars = dict(navbar=create_navbar(create_navbar_links(objs, stats, wd)), sample_name=sample_name,
                                 stats_file_path=stats_file_path, profile_file_path=profile_file_path,
                                 commands_file_path=commands_file_path, log_file_path=log_file_path,
                                 button_class=button_class, sample_stats=sample_stats, flag=flag, links=links,
                                 figures=figures, version=v)
            save_html(html_page, self.render_jinja_template("sample.html", template_vars))
            return sample_page_relpath

        def create_status_html(objs, stats, wd):
            """
            Generates a page listing all the samples, their run status, their
            log file, and the total runtime if completed.

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
            :return str: rendered status HTML file
            """
            _LOGGER.debug("Building status page...")
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
            table_appearance_by_flag = {
                "completed": {
                    "button_class": "table-success",
                    "flag": "Completed"
                },
                "running": {
                    "button_class": "table-warning",
                    "flag": "Running"
                },
                "failed": {
                    "button_class": "table-danger",
                    "flag": "Failed"
                }
            }
            for sample in self.prj.samples:
                sample_name = str(sample.sample_name)
                sample_dir = os.path.join(
                    self.prj.metadata.results_subdir, sample_name)

                # Confirm sample directory exists, then build page
                if os.path.exists(sample_dir):
                    # Grab the status flag for the current sample
                    flag = _get_flags(sample_dir)
                    if not flag:
                        button_class = "table-danger"
                        flag = "Missing"
                    elif len(flag) > 1:
                        button_class = "table-warning"
                        flag = "Multiple"
                    else:
                        flag = flag[0]
                        try:
                            flag_dict = table_appearance_by_flag[flag]
                        except KeyError:
                            button_class = "table-secondary"
                            flag = "Unknown"
                        else:
                            button_class = flag_dict["button_class"]
                            flag = flag_dict["flag"]

                    # get first column data (sample name/link)
                    page_name = sample_name + ".html"
                    page_path = os.path.join(self.reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, self.reports_dir)
                    sample_paths.append(page_relpath)
                    sample_link_names.append(sample_name)
                    # get second column data (status/flag)
                    flags.append(flag)
                    # get third column data (log file/link)
                    single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
                    log_name = _match_file_for_sample(sample_name, "log.md", self.prj.metadata.results_subdir) \
                        if single_sample.empty else str(single_sample.iloc[0]['annotation']) + "_log.md"
                    log_file = os.path.join(self.prj.metadata.results_subdir, sample_name, log_name)
                    file_link = _get_relpath_to_file(
                        log_name, sample_name, self.prj.metadata.results_subdir, self.reports_dir)
                    log_link_names.append(log_name)
                    log_paths.append(file_link)
                    # get fourth column data (runtime)
                    time = "Unknown"
                    if os.path.isfile(log_file):
                        t = _pd.read_table(log_file, header=None, names=['key', 'value'])
                        t.drop_duplicates(subset=['value'], keep='last', inplace=True)
                        t['key'] = t['key'].str.replace('> `', '')
                        t['key'] = t['key'].str.replace('`', '')
                        try:
                            time = str(t[t['key'] == 'Time'].iloc[0]['value'])
                        except IndexError:
                            status_warning = True
                    times.append(time)
                    # get fifth column data (memory use)
                    mem = "NA"
                    if os.path.isfile(log_file):
                        m = _pd.read_table(log_file, header=None, sep=':', names=['key', 'value'])
                        m.drop_duplicates(subset=['value'], keep='last', inplace=True)
                        m['key'] = m['key'].str.replace('*', '')
                        m['key'] = m['key'].str.replace('^\s+', '')
                        try:
                            mem = str(m[m['key'] == 'Peak memory used'].iloc[0]['value']).replace(' ', '')
                        except IndexError:
                            status_warning = True
                    mems.append(mem)
                    row_classes.append(button_class)
                else:
                    # Sample was not run through the pipeline
                    sample_warning.append(sample_name)

            # Alert the user to any warnings generated
            if status_warning:
                _LOGGER.warning("The stats table is incomplete, likely because " +
                                "one or more jobs either failed or is still running.")

            if sample_warning:
                if len(sample_warning) == 1:
                    _LOGGER.warning("{} is not present in {}".format(
                        ''.join(str(sample) for sample in sample_warning),
                        self.prj.metadata.results_subdir))
                else:
                    warn_msg = "The following samples are not present in {}: {}"
                    _LOGGER.warning(warn_msg.format(
                        self.prj.metadata.results_subdir,
                        ' '.join(str(sample) for sample in sample_warning)))

            template_vars = dict(navbar=create_navbar(create_navbar_links(objs, stats, wd)), sample_link_names=sample_link_names,
                             sample_paths=sample_paths, log_link_names=log_link_names, log_paths=log_paths,
                             row_classes=row_classes, flags=flags, times=times, mems=mems, version=v)
            return self.render_jinja_template("status.html", template_vars)

        def _get_navbar_dropdown_data_objects(objs, rep_dir, wd):
            relpaths = []
            df_keys = objs['key'].drop_duplicates().sort_values()
            for key in df_keys:
                page_name = key + ".html"
                page_path = os.path.join(rep_dir, page_name.replace(' ', '_').lower())
                relpaths.append(os.path.relpath(page_path, wd))
            return relpaths, df_keys

        def _get_navbar_dropdown_data_samples(stats, rep_dir, wd):
            relpaths = []
            sample_names = []
            for sample in stats:
                for entry, val in sample.items():
                    if entry == "sample_name":
                        sample_name = str(val)
                        page_name = sample_name + ".html"
                        page_path = os.path.join(rep_dir, page_name.replace(' ', '_').lower())
                        relpath = os.path.relpath(page_path, wd)
                        relpaths.append(relpath)
                        sample_names.append(sample_name)
                        break
                    else:
                        _LOGGER.warning("Could not determine sample name in stats.tsv")
            return relpaths,  sample_names

        def create_navbar_links(objs, stats, wd):
            """
            Return a string containing the navbar prebuilt html.
            Generates links to each page relative to the directory
            of interest.
            :param pandas.DataFrame objs: project results dataframe containing
                object data
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param path wd: the working directory of the current HTML page
                being generated, enables navbar links relative to page
            """
            _LOGGER.debug("Building navbar with paths relative to: {}...".format(wd))
            index_html_path = get_index_html_path()
            index_page_relpath = os.path.relpath(index_html_path, wd)
            status_page = os.path.join(self.reports_dir, "status.html")
            status_relpath = os.path.relpath(status_page, wd)
            objects_page = os.path.join(self.reports_dir, "objects.html")
            objects_relpath = os.path.relpath(objects_page, wd)
            samples_page = os.path.join(self.reports_dir, "samples.html")
            samples_relpath = os.path.relpath(samples_page, wd)
            dropdown_keys_objects = None
            dropdown_relpaths_objects = None
            dropdown_relpaths_samples = None
            sample_names = None
            if not objs.dropna().empty:
                # If the number of objects is 20 or less, use a drop-down menu
                if len(objs['key'].drop_duplicates()) <= 20:
                    navbar_dropdown_data_objects = _get_navbar_dropdown_data_objects(objs, self.reports_dir, wd)
                    dropdown_relpaths_objects = navbar_dropdown_data_objects[0]
                    dropdown_keys_objects = navbar_dropdown_data_objects[1]
                else:
                    dropdown_relpaths_objects = objects_relpath
            if stats:
                if len(stats) <= 20:
                    navbar_dropdown_data_samples = _get_navbar_dropdown_data_samples(stats, self.reports_dir, wd)
                    dropdown_relpaths_samples = navbar_dropdown_data_samples[0]
                    sample_names = navbar_dropdown_data_samples[1]
                else:
                    # Create a menu link to the samples parent page
                    dropdown_relpaths_samples = samples_relpath
            template_vars = dict(index_html=index_page_relpath, status_html_page=status_relpath,
                                 status_page_name="Status", dropdown_keys_objects=dropdown_keys_objects,
                                 objects_page_name="Objects", samples_page_name="Samples",
                                 objects_html_page=dropdown_relpaths_objects,
                                 samples_html_page=dropdown_relpaths_samples, menu_name_objects="Objects",
                                 menu_name_samples="Samples", sample_names=sample_names, all_samples=samples_relpath,
                                 all_objects=objects_relpath)
            return self.render_jinja_template("navbar_links.html", template_vars)

        def create_navbar(navbar_links):
            template_vars = dict(navbar_links=navbar_links)
            return self.render_jinja_template("navbar.html", template_vars)

        def create_project_objects():
            _LOGGER.debug("Building project object...")
            """ Render available project level summaries as additional figures/links """

            all_protocols = [sample.protocol for sample in self.prj.samples]

            # For each protocol report the project summarizers' results
            for protocol in set(all_protocols):
                figures = []
                links = []
                warnings = []
                ifaces = self.prj.interfaces_by_protocol[protocol]

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
            return self.render_jinja_template("project_object.html", template_vars)

        def create_index_html(objs, stats, col_names):
            """
            Generate an index.html style project home page w/ sample summary
            statistics

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            """
            _LOGGER.debug("Building index page...")

            if not objs.dropna().empty:
                objs.drop_duplicates(keep='last', inplace=True)
            # Generate parent index.html page path
            index_html_path = get_index_html_path()

            # Add stats_summary.tsv button link
            tsv_outfile_path = os.path.join(self.prj.metadata.output_dir, self.prj.name)
            if hasattr(self.prj, "subproject") and self.prj.subproject:
                tsv_outfile_path += '_' + self.prj.subproject
            tsv_outfile_path += '_stats_summary.tsv'
            stats_file_path = os.path.relpath(tsv_outfile_path, self.prj.metadata.output_dir)
            # Add stats summary table to index page and produce individual
            # sample pages
            if os.path.isfile(tsv_outfile_path):
                # Produce table rows
                sample_pos = 0
                col_pos = 0
                num_columns = len(col_names)
                table_row_data = []
                for row in stats:
                    # Match row value to column
                    # Row is disordered and does not handle empty cells
                    table_row = []
                    while col_pos < num_columns:
                        value = row.get(col_names[col_pos])
                        if value is None:
                            value = ''
                        table_row.append(value)
                        col_pos += 1
                    # Reset column position counter
                    col_pos = 0
                    sample_name = str(stats[sample_pos]['sample_name'])
                    # Order table_row by col_names
                    sample_stats = OrderedDict(zip(col_names, table_row))
                    table_cell_data = []
                    for value in table_row:
                        if value == sample_name:
                            # Generate individual sample page and return link
                            sample_page = create_sample_html(objs, stats, sample_name, sample_stats, self.reports_dir)
                            # Treat sample_name as a link to sample page
                            data = [sample_page, sample_name]
                        # If not the sample name, add as an unlinked cell value
                        else:
                            data = str(value)
                        table_cell_data.append(data)
                    sample_pos += 1
                    table_row_data.append(table_cell_data)
            else:
                _LOGGER.warning("No stats file '%s'", tsv_outfile_path)

            # Create parent samples page with links to each sample
            save_html(os.path.join(self.reports_dir, "samples.html"),
                      create_sample_parent_html(objs, stats, self.reports_dir))

            # Create objects pages
            if not objs.dropna().empty:
                for key in objs['key'].drop_duplicates().sort_values():
                    single_object = objs[objs['key'] == key]
                    create_object_html(single_object, objs, stats, self.reports_dir)

            # Create parent objects page with links to each object type
            save_html(os.path.join(self.reports_dir, "objects.html"),
                      create_object_parent_html(objs, stats, self.reports_dir))
            # Create status page with each sample's status listed
            save_html(os.path.join(self.reports_dir, "status.html"),
                      create_status_html(objs, stats, self.reports_dir))
            # Add project level objects
            project_objects = create_project_objects()
            # Complete and close HTML file
            template_vars = dict(project_name=self.prj.name, stats_json=_read_tsv_to_json(tsv_outfile_path),
                                 navbar=create_navbar(create_navbar_links(objs, stats, self.prj.metadata.output_dir)),
                                 stats_file_path=stats_file_path, project_objects=project_objects, columns=col_names,
                                 table_row_data=table_row_data, version=v)
            save_html(index_html_path, self.render_jinja_template("index.html", template_vars))
            return index_html_path
        # Generate HTML report
        index_html_path = create_index_html(objs, stats, columns)
        return index_html_path

    def render_jinja_template(self, name, args=dict()):
        """

        :param str name: name of the template
        :param dict args: arguments to pass to the template
        :return str: rendered template
        """
        assert isinstance(args, dict), "args has to be a dict"
        template = self.j_env.get_template(name)
        return template.render(**args)

    def get_reports_dir(self):
        """
        Get the reports directory path depending on the subproject activation status

        :return str: path to the reports directory
        """
        rep_dir_name = "reports" if self.prj.subproject is None else "reports_" + self.prj.subproject
        return os.path.join(self.prj.metadata.output_dir, rep_dir_name)


def save_html(path, template):
    """
    Save rendered template as an HTML file

    :param str path: the desired location for the file to be produced
    :param str template: the template or just string
    """

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    try:
        f = open(path, 'w')
    except IOError:
        _LOGGER.error("Could not write the HTML file: {}".format(path))

    with f:
        f.write(template)


def get_templates_dir():
    file_dir = os.path.dirname(__file__)
    jinja_templ_dir = os.path.join(file_dir, TEMPLATES_DIRNAME)
    _LOGGER.info("using templates dir: " + jinja_templ_dir)
    return jinja_templ_dir


def get_jinja_env():
    return jinja2.Environment(loader=jinja2.FileSystemLoader(get_templates_dir()))


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


def _match_file_for_sample(sample_name, appendix, location):
    """
    Safely looks for files matching the appendix in the specified location for the sample

    :param str sample_name: name of the sample that the file name should be found for
    :param str appendix: the ending  specific for the file
    :param str location: where to look for the file
    :return str: the name of the matched file
    """
    regex = "*" + appendix
    search_pattern = os.path.join(location, sample_name, regex)
    matches = glob.glob(search_pattern)
    if len(matches) < 1:
        return None
    elif len(matches) > 1:
        _LOGGER.warning("matched mutiple files for '{}'. Returning the first one".format(search_pattern))
    return os.path.basename(matches[0])


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
    _LOGGER.debug("Checking for file: '{fp}'. Exists? {exists}.".
                  format(fp=abs_file_path, exists=os.path.exists(abs_file_path)))
    if file_name is None or not os.path.exists(abs_file_path):
        return None
    return rel_file_path


def _read_tsv_to_json(path):
    """
    Read a tsv file to a JSON formatted string

    :param path: to file path
    :return str: JSON formatted string
    """
    assert os.path.exists(path), "The file '{}' does not exist".format(path)
    _LOGGER.debug("Reading TSV from '{}'".format(path))
    df = _pd.read_table(path, sep="\t", index_col=False, header=None)
    return df.to_json()

def uniqify(seq):
    """ Fast way to uniqify while preserving input order. """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


