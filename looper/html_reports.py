""" Generate HTML reports """

import os
import glob
import pandas as _pd
import logging
import jinja2
import re

from _version import __version__ as v
from collections import OrderedDict

_LOGGER = logging.getLogger('HTMLReportBuilder')

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"
NAVBAR_LOGO = \
    """\
    data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhLS0gQ3JlYXRlZCB3aXRoIElua3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoKPHN2ZwogICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgIHhtbG5zOmNjPSJodHRwOi8vY3JlYXRpdmVjb21tb25zLm9yZy9ucyMiCiAgIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJjZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB3aWR0aD0iNjMuODg1MTM2bW0iCiAgIGhlaWdodD0iNTguNTA0NzA3bW0iCiAgIHZpZXdCb3g9IjAgMCAyMjYuMzY0NjUgMjA3LjMwMDEzIgogICBpZD0ic3ZnNDE5OCIKICAgdmVyc2lvbj0iMS4xIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkxIHIxMzcyNSIKICAgc29kaXBvZGk6ZG9jbmFtZT0ibG9nb19sb29wZXIuc3ZnIj4KICA8ZGVmcwogICAgIGlkPSJkZWZzNDIwMCIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgaWQ9ImJhc2UiCiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEuMCIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgIGlua3NjYXBlOnBhZ2VzaGFkb3c9IjIiCiAgICAgaW5rc2NhcGU6em9vbT0iMi44Mjg0MjcxIgogICAgIGlua3NjYXBlOmN4PSI4MC45NTQ1MzIiCiAgICAgaW5rc2NhcGU6Y3k9IjIyOS42MjgxOCIKICAgICBpbmtzY2FwZTpkb2N1bWVudC11bml0cz0icHgiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ibGF5ZXIxIgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBmaXQtbWFyZ2luLXRvcD0iMiIKICAgICBmaXQtbWFyZ2luLWxlZnQ9IjMiCiAgICAgZml0LW1hcmdpbi1yaWdodD0iMyIKICAgICBmaXQtbWFyZ2luLWJvdHRvbT0iMiIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGE0MjAzIj4KICAgIDxyZGY6UkRGPgogICAgICA8Y2M6V29yawogICAgICAgICByZGY6YWJvdXQ9IiI+CiAgICAgICAgPGRjOmZvcm1hdD5pbWFnZS9zdmcreG1sPC9kYzpmb3JtYXQ+CiAgICAgICAgPGRjOnR5cGUKICAgICAgICAgICByZGY6cmVzb3VyY2U9Imh0dHA6Ly9wdXJsLm9yZy9kYy9kY21pdHlwZS9TdGlsbEltYWdlIiAvPgogICAgICAgIDxkYzp0aXRsZT48L2RjOnRpdGxlPgogICAgICA8L2NjOldvcms+CiAgICA8L3JkZjpSREY+CiAgPC9tZXRhZGF0YT4KICA8ZwogICAgIGlua3NjYXBlOmxhYmVsPSJMYXllciAxIgogICAgIGlua3NjYXBlOmdyb3VwbW9kZT0ibGF5ZXIiCiAgICAgaWQ9ImxheWVyMSIKICAgICB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMjc4LjI0NjI0LC04NTQuNDI2NDIpIj4KICAgIDxwYXRoCiAgICAgICBzdHlsZT0iZmlsbDojNWY4ZGQzO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmUiCiAgICAgICBpZD0icGF0aDQxNDYiCiAgICAgICBkPSJtIDM0NS40MjUyNCw5OTMuMDc5MDQgYyA2LjE1MSwwIDEyLjQwOCwtMS4wMTQgMTguNTM2LC0zLjE0NyBsIC00LjYwOCwtMTMuMjIxIGMgLTIyLjEyNiw3LjcwMyAtNDYuMzk5LC00LjAyMSAtNTQuMTA1LC0yNi4xNCAtNy43MTEsLTIyLjEyMDAxIDQuMDE1LC00Ni4zOTEwMSAyNi4xMzcsLTU0LjEwMzAxIDguMzI3LC0yLjkwMiAxNy4xNzcsLTMuMTM1IDI1LjUxMywtMC43NyBsIC0xNS4yNiw4LjA4MyA2LjU1NCwxMi4zNzIgMzYuNTQ4MDEsLTE5LjM2IC0yMi4yMDMwMSwtMzUuMjggLTExLjg0OSw3LjQ1NiA4LjAwMywxMi43MTkgYyAtMTAuNDg3LC0yLjU2MyAtMjEuNTA5LC0yLjA2NCAtMzEuOTE1LDEuNTYyIC0yOS40MTIsMTAuMjUzIC00NS4wMDAwMSw0Mi41MjEgLTM0Ljc0OTAxLDcxLjkzMDAxIDguMTEyMDEsMjMuMjggMzAuMDIyMDEsMzcuODk5IDUzLjM5ODAxLDM3Ljg5OSB6IgogICAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIKICAgICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0ic2NjY2NjY2NjY2NjY2NzIiAvPgogICAgPHJlY3QKICAgICAgIHN0eWxlPSJjb2xvcjojMDAwMDAwO2NsaXAtcnVsZTpub256ZXJvO2Rpc3BsYXk6aW5saW5lO292ZXJmbG93OnZpc2libGU7dmlzaWJpbGl0eTp2aXNpYmxlO29wYWNpdHk6MTtpc29sYXRpb246YXV0bzttaXgtYmxlbmQtbW9kZTpub3JtYWw7Y29sb3ItaW50ZXJwb2xhdGlvbjpzUkdCO2NvbG9yLWludGVycG9sYXRpb24tZmlsdGVyczpsaW5lYXJSR0I7c29saWQtY29sb3I6IzAwMDAwMDtzb2xpZC1vcGFjaXR5OjE7ZmlsbDojNWY4ZGQzO2ZpbGwtb3BhY2l0eToxO2ZpbGwtcnVsZTpub256ZXJvO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLWxpbmVjYXA6YnV0dDtzdHJva2UtbGluZWpvaW46bWl0ZXI7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmU7c3Ryb2tlLWRhc2hvZmZzZXQ6MDtzdHJva2Utb3BhY2l0eToxO21hcmtlcjpub25lO2NvbG9yLXJlbmRlcmluZzphdXRvO2ltYWdlLXJlbmRlcmluZzphdXRvO3NoYXBlLXJlbmRlcmluZzphdXRvO3RleHQtcmVuZGVyaW5nOmF1dG87ZW5hYmxlLWJhY2tncm91bmQ6YWNjdW11bGF0ZSIKICAgICAgIGlkPSJyZWN0NDE1NyIKICAgICAgIHdpZHRoPSI0NC4wMzc0NDkiCiAgICAgICBoZWlnaHQ9IjExLjAwOTgxMiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgeT0iOTIyLjc4NjMyIiAvPgogICAgPHJlY3QKICAgICAgIHk9IjkzOS41NTQyNiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgaGVpZ2h0PSIxMS4wMDk4MTIiCiAgICAgICB3aWR0aD0iNDQuMDM3NDQ5IgogICAgICAgaWQ9InJlY3Q0MTU5IgogICAgICAgc3R5bGU9ImNvbG9yOiMwMDAwMDA7Y2xpcC1ydWxlOm5vbnplcm87ZGlzcGxheTppbmxpbmU7b3ZlcmZsb3c6dmlzaWJsZTt2aXNpYmlsaXR5OnZpc2libGU7b3BhY2l0eToxO2lzb2xhdGlvbjphdXRvO21peC1ibGVuZC1tb2RlOm5vcm1hbDtjb2xvci1pbnRlcnBvbGF0aW9uOnNSR0I7Y29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzOmxpbmVhclJHQjtzb2xpZC1jb2xvcjojMDAwMDAwO3NvbGlkLW9wYWNpdHk6MTtmaWxsOiM1ZjhkZDM7ZmlsbC1vcGFjaXR5OjE7ZmlsbC1ydWxlOm5vbnplcm87c3Ryb2tlOiNmZmZmZmY7c3Ryb2tlLXdpZHRoOjEuNTtzdHJva2UtbGluZWNhcDpidXR0O3N0cm9rZS1saW5lam9pbjptaXRlcjtzdHJva2UtbWl0ZXJsaW1pdDo0O3N0cm9rZS1kYXNoYXJyYXk6bm9uZTtzdHJva2UtZGFzaG9mZnNldDowO3N0cm9rZS1vcGFjaXR5OjE7bWFya2VyOm5vbmU7Y29sb3ItcmVuZGVyaW5nOmF1dG87aW1hZ2UtcmVuZGVyaW5nOmF1dG87c2hhcGUtcmVuZGVyaW5nOmF1dG87dGV4dC1yZW5kZXJpbmc6YXV0bztlbmFibGUtYmFja2dyb3VuZDphY2N1bXVsYXRlIiAvPgogICAgPHJlY3QKICAgICAgIHN0eWxlPSJjb2xvcjojMDAwMDAwO2NsaXAtcnVsZTpub256ZXJvO2Rpc3BsYXk6aW5saW5lO292ZXJmbG93OnZpc2libGU7dmlzaWJpbGl0eTp2aXNpYmxlO29wYWNpdHk6MTtpc29sYXRpb246YXV0bzttaXgtYmxlbmQtbW9kZTpub3JtYWw7Y29sb3ItaW50ZXJwb2xhdGlvbjpzUkdCO2NvbG9yLWludGVycG9sYXRpb24tZmlsdGVyczpsaW5lYXJSR0I7c29saWQtY29sb3I6IzAwMDAwMDtzb2xpZC1vcGFjaXR5OjE7ZmlsbDojNWY4ZGQzO2ZpbGwtb3BhY2l0eToxO2ZpbGwtcnVsZTpub256ZXJvO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLWxpbmVjYXA6YnV0dDtzdHJva2UtbGluZWpvaW46bWl0ZXI7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmU7c3Ryb2tlLWRhc2hvZmZzZXQ6MDtzdHJva2Utb3BhY2l0eToxO21hcmtlcjpub25lO2NvbG9yLXJlbmRlcmluZzphdXRvO2ltYWdlLXJlbmRlcmluZzphdXRvO3NoYXBlLXJlbmRlcmluZzphdXRvO3RleHQtcmVuZGVyaW5nOmF1dG87ZW5hYmxlLWJhY2tncm91bmQ6YWNjdW11bGF0ZSIKICAgICAgIGlkPSJyZWN0NDE2MSIKICAgICAgIHdpZHRoPSI0NC4wMzc0NDkiCiAgICAgICBoZWlnaHQ9IjExLjAwOTgxMiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgeT0iOTU2LjMyMjIiIC8+CiAgICA8cGF0aAogICAgICAgc3R5bGU9ImZpbGw6IzVmOGRkMztzdHJva2U6I2ZmZmZmZjtzdHJva2Utd2lkdGg6MS41O3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpub25lIgogICAgICAgaWQ9InBhdGg0MTY3IgogICAgICAgZD0ibSA0OTIuMDAzODQsMTAzMi41MjM2IGMgLTQuMDAwMjYsLTguNjkwMiAtOC45MjAxMSwtMjIuODA2MSAtOS43MDE3NywtMzMuOTMzMjMgbCAtMC41MDU3OCwtNy4wODA5MSAtNy44NjI1OCwxNi43ODI2NCAtMTcuMTA0NTQsLTE3LjEwNDUgOS4wODA5MSwwIGMgNi41NzUxNCwwIDExLjk1NDc5LC01LjM3OTY2IDExLjk1NDc5LC0xMS45NTQ3OSBsIDAsLTU5LjYxNDQ0IGMgMCwtNi41NzUxMyAtNS4zNzk2NSwtMTEuOTU0NzkgLTExLjk1NDc5LC0xMS45NTQ3OSBsIC03Ni45Mjg4NCwwIGMgLTYuNTc1MTMsMCAtMTEuOTU0NzksNS4zNzk2NiAtMTEuOTU0NzksMTEuOTU0NzkgbCAwLDU5LjYxNDQ0IGMgMCw2LjU3NTEzIDUuMzc5NjYsMTEuOTU0NzkgMTEuOTU0NzksMTEuOTU0NzkgbCAzLjMxMDU2LDAgLTE3LjEwNDU0LDE3LjEwNDUgLTcuODYyNTgsLTE2Ljc4MjY0IC0wLjUwNTc4LDcuMDgwOTEgYyAtMC43ODE2NiwxMS4xMjcxMyAtNS43MDE1MiwyNS4yNDMwMyAtOS43MDE3NywzMy45MzMyMyBsIC0yLjA2OTEsNC41MDYgNC41MDYwNCwtMi4wNjkxIGMgOC42OTAyMSwtNC4wMDAyIDIyLjgwNjA2LC04LjkyMDEgMzMuOTMzMjEsLTkuNzAxNyBsIDcuMDgwOTEsLTAuNTA1OCAtMTYuNzgyNjgsLTcuODYyNiAyNS4yNDMsLTI1LjI0MyBjIDAuMTM3OTQsLTAuMTM3OTQgMC4yNzU4OCwtMC4zMjE4NiAwLjQxMzgyLC0wLjUwNTc4IGwgOS4xNTIzMiwwIDAsMjguOTY3MzggLTE3LjQyNjQsLTYuMjk5MyA0LjY4OTk1LDUuMzMzNyBjIDcuMzEwODIsOC40MTQzIDEzLjc5Mzk5LDIxLjg0MDUgMTcuMTUwNTMsMzAuODUyNiBsIDEuNzQ3MjQsNC42NDM5IDEuNzAxMjYsLTQuNjQzOSBjIDMuMzEwNTUsLTguOTY2MSA5Ljc5MzczLC0yMi40MzgzIDE3LjE1MDUyLC0zMC44NTI2IGwgNC42ODk5NiwtNS4zMzM3IC0xNy40MjY0MSw2LjI5OTMgMCwtMjguOTY3MzggOC43MTUzOCwwIGMgMC4xMzc5NCwwLjE4MzkyIDAuMjc1ODgsMC4zMjE4NiAwLjQxMzgyLDAuNTA1NzggbCAyNS4yNDMsMjUuMjQzIC0xNi43ODI2OSw3Ljg2MjYgNy4wODA5MiwwLjUwNTggYyAxMS4xMjcxNSwwLjc4MTYgMjUuMjQzLDUuNzAxNSAzMy45MzMyMSw5LjcwMTcgbCA0LjUwNjA0LDIuMDY5MSB6IG0gLTEwMi4xMDMsLTExMS45ODU2MyA3NS4xMzU2MiwwIDAsNTcuNzc1MjQgLTc1LjEzNTYyLDAgeiIKICAgICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiCiAgICAgICBzb2RpcG9kaTpub2RldHlwZXM9ImNjY2Njc3Nzc3Nzc3NjY2NjY2NjY2Njc2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2MiIC8+CiAgPC9nPgo8L3N2Zz4K\
    """
TEMPLATES_DIRNAME = "jinja_templates"
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

    def __call__(self, objs, stats, columns):
        """ Do the work of the subcommand/program. """

        def get_reports_dir():
            """
            Get the reports directory path depending on the subproject activation status

            :return str: path to the reports directory
            """
            rep_dir_name = "reports" if self.prj.subproject is None else "reports_" + self.prj.subproject
            return os.path.join(self.prj.metadata.output_dir, rep_dir_name)

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
            reports_dir = get_reports_dir()
            object_parent_path = os.path.join(reports_dir, "objects.html")

            if not os.path.exists(os.path.dirname(object_parent_path)):
                os.makedirs(os.path.dirname(object_parent_path))
            pages = list()
            labels = list()
            if not objs.empty:
                for key in objs['key'].drop_duplicates().sort_values():
                    page_name = key + ".html"
                    page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    pages.append(page_relpath)
                    labels.append(key)

            template_vars = dict(navbar=create_navbar(objs, stats, wd), labels=labels, pages=pages, header="Objects", version=v)
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
            reports_dir = get_reports_dir()
            sample_parent_path = os.path.join(reports_dir, "samples.html")

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
                    page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    pages.append(page_relpath)
                    labels.append(sample_name)

            template_vars = dict(navbar=create_navbar(objs, stats, wd), labels=labels, pages=pages, header="Samples", version=v)
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

            reports_dir = get_reports_dir()

            # Generate object filename
            for key in single_object['key'].drop_duplicates().sort_values():
                # even though it's always one element, loop to extract the data
                current_name = str(key)
                filename = current_name + ".html"
            object_path = os.path.join(reports_dir, filename.replace(' ', '_').lower())

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
                    page_relpath = os.path.relpath(page_path, reports_dir)
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
                    image_relpath = os.path.relpath(image_path, reports_dir)
                    _LOGGER.debug(str(image_relpath))
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
            template_vars = dict(navbar=create_navbar(objs, stats, wd), name=current_name, figures=figures, links=links, version=v)
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
            reports_dir = get_reports_dir()
            html_filename = sample_name + ".html"
            html_page = os.path.join(reports_dir, html_filename.replace(' ', '_').lower())
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
                    log_name = os.path.basename(str(glob.glob(os.path.join(
                        self.prj.metadata.results_subdir,
                        sample_name, '*log.md'))[0]))
                    profile_name = os.path.basename(str(glob.glob(os.path.join(
                        self.prj.metadata.results_subdir,
                        sample_name, '*profile.tsv'))[0]))
                    command_name = os.path.basename(str(glob.glob(os.path.join(
                        self.prj.metadata.results_subdir,
                        sample_name, '*commands.sh'))[0]))
                else:
                    log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                    profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                    command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
                flag = get_flags(sample_dir)
                _LOGGER.debug("Flag(s) found for sample {s}: {f}".format(s=sample_name, f=", ".join(flag)))
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
                # get links to the files
                stats_file_path = os.path.relpath(os.path.join(
                    self.prj.metadata.results_subdir, sample_name, "stats.tsv"), reports_dir)
                profile_file_path = os.path.relpath(os.path.join(
                    self.prj.metadata.results_subdir, sample_name, profile_name), reports_dir)
                commands_file_path = os.path.relpath(os.path.join(
                    self.prj.metadata.results_subdir, sample_name, command_name), reports_dir)
                log_file_path = os.path.relpath(os.path.join(
                    self.prj.metadata.results_subdir, sample_name, log_name), reports_dir)

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
                            image_relpath = os.path.relpath(image_path, reports_dir)
                        except AttributeError:
                            image_path = ""
                            image_relpath = ""

                        # These references to "page" should really be
                        # "object", because they can be anything.
                        page_path = os.path.join(
                            self.prj.metadata.results_subdir,
                            sample_name, row['filename'])
                        page_relpath = os.path.relpath(page_path, reports_dir)
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

            template_vars = dict(navbar=create_navbar(objs, stats, wd), sample_name=sample_name, stats_file_path=stats_file_path, profile_file_path=profile_file_path, commands_file_path=commands_file_path, log_file_path=log_file_path, button_class=button_class, sample_stats=sample_stats, flag=flag, links=links, figures=figures, version=v)
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
            reports_dir = get_reports_dir()
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
                    flag = get_flags(sample_dir)
                    _LOGGER.debug("Flag(s) found for sample {s}: {f}".format(s=sample, f=", ".join(flag)))
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
                    page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    sample_paths.append(page_relpath)
                    sample_link_names.append(sample_name)
                    # get second column data (status/flag)
                    flags.append(flag)
                    # get third column data (log file/link)
                    single_sample = _pd.DataFrame() if objs.empty else objs[objs['sample_name'] == sample_name]
                    log_name = os.path.basename(str(glob.glob(os.path.join(
                        self.prj.metadata.results_subdir, sample_name, '*log.md'))[0])) if single_sample.empty \
                        else str(single_sample.iloc[0]['annotation']) + "_log.md"
                    log_file = os.path.join(self.prj.metadata.results_subdir, sample_name, log_name)
                    file_link = os.path.relpath(log_file, reports_dir) if os.path.isfile(log_file) else ""
                    link_name = log_name if os.path.isfile(log_file) else ""
                    log_link_names.append(link_name)
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

            template_vars = dict(navbar=create_navbar(objs, stats, wd), sample_link_names=sample_link_names,
                             sample_paths=sample_paths, log_link_names=log_link_names, log_paths=log_paths,
                             row_classes=row_classes, flags=flags, times=times, mems=mems, version=v)
            return self.render_jinja_template("status.html", template_vars)

        def _get_navbar_dropdown_data_objects(objs, reports_dir, wd):
            relpaths = []
            df_keys = objs['key'].drop_duplicates().sort_values()
            for key in df_keys:
                page_name = key + ".html"
                page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                relpaths.append(os.path.relpath(page_path, wd))
            return relpaths, df_keys

        def _get_navbar_dropdown_data_samples(stats, reports_dir, wd):
            relpaths = []
            sample_names = []
            for sample in stats:
                for entry, val in sample.items():
                    if entry == "sample_name":
                        sample_name = str(val)
                        page_name = sample_name + ".html"
                        page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                        relpath = os.path.relpath(page_path, wd)
                        relpaths.append(relpath)
                        sample_names.append(sample_name)
                        break
                    else:
                        _LOGGER.warning("Could not determine sample name in stats.tsv")
            return relpaths,  sample_names

        def create_navbar(objs, stats, wd):
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
            # paths
            index_html_path = get_index_html_path()
            reports_dir = get_reports_dir()
            index_page_relpath = os.path.relpath(index_html_path, wd)
            status_page = os.path.join(reports_dir, "status.html")
            status_relpath = os.path.relpath(status_page, wd)
            objects_page = os.path.join(reports_dir, "objects.html")
            objects_relpath = os.path.relpath(objects_page, wd)
            samples_page = os.path.join(reports_dir, "samples.html")
            samples_relpath = os.path.relpath(samples_page, wd)
            dropdown_keys_objects = dropdown_relpaths_objects = dropdown_relpaths_samples = sample_names = None
            if not objs.dropna().empty:
                # If the number of objects is 20 or less, use a drop-down menu
                if len(objs['key'].drop_duplicates()) <= 20:
                    navbar_dropdown_data_objects = _get_navbar_dropdown_data_objects(objs, reports_dir, wd)
                    dropdown_relpaths_objects = navbar_dropdown_data_objects[0]
                    dropdown_keys_objects = navbar_dropdown_data_objects[1]
                else:
                    dropdown_relpaths_objects = objects_relpath
            if stats:
                if len(stats) <= 20:
                    navbar_dropdown_data_samples = _get_navbar_dropdown_data_samples(stats, reports_dir, wd)
                    dropdown_relpaths_samples = navbar_dropdown_data_samples[0]
                    sample_names = navbar_dropdown_data_samples[1]
                else:
                    # Create a menu link to the samples parent page
                    dropdown_relpaths_samples = samples_relpath
            template_vars = dict(logo=NAVBAR_LOGO, index_html=index_page_relpath, status_html_page=status_relpath,
                                    status_page_name="Status", dropdown_keys_objects=dropdown_keys_objects,
                                    objects_page_name="Objects", samples_page_name="Samples",
                                    objects_html_page=dropdown_relpaths_objects,
                                    samples_html_page=dropdown_relpaths_samples, menu_name_objects="Objects",
                                    menu_name_samples="Samples", sample_names=sample_names, all_samples=samples_relpath,
                                    all_objects=objects_relpath, version=v)
            return self.render_jinja_template("my_navbar.html", template_vars)

        def create_project_objects():
            """ Add project level summaries as additional figures/links """

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
                                    figures.append([file_relpath, '{}: Click to see full-size figure'.format(caption), img_relpath])
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

        def create_project_objects_old():
            """ Add project level summaries as additional figures/links """

            all_protocols = [sample.protocol for sample in self.prj.samples]

            # For each protocol report the project summarizers' results
            for protocol in set(all_protocols):
                obj_figs = []
                num_figures = 0
                obj_links = []
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
                            result_file = str(result['path']).replace(
                                            '{name}', str(self.prj.name))
                            result_img = str(result['thumbnail_path']).replace(
                                            '{name}', str(self.prj.name))
                            search = os.path.join(self.prj.metadata.output_dir,
                                                  '{}'.format(result_file))

                            # Confirm the file itself was produced
                            if glob.glob(search):
                                file_path = str(glob.glob(search)[0])
                                file_relpath = os.path.relpath(
                                                file_path,
                                                self.prj.metadata.output_dir)
                                search = os.path.join(self.prj.metadata.output_dir,
                                                      '{}'.format(result_img))

                                # Add as a figure if thumbnail exists
                                if glob.glob(search):
                                    img_path = str(glob.glob(search)[0])
                                    img_relpath = os.path.relpath(
                                                    img_path,
                                                    self.prj.metadata.output_dir)

                                    # Add to single row
                                    if num_figures < 3:
                                        obj_figs.append(HTML_FIGURE.format(
                                            path=file_relpath,
                                            image=img_relpath,
                                            label='{}: Click to see full-size figure'.format(caption)))
                                        num_figures += 1

                                    # Close the previous row and start a new one
                                    else:
                                        num_figures = 1
                                        obj_figs.append("\t\t\t</div>")
                                        obj_figs.append("\t\t\t<div class='row justify-content-start'>")
                                        obj_figs.append(HTML_FIGURE.format(
                                            path=file_relpath,
                                            image=img_relpath,
                                            label='{}: Click to see full-size figure'.format(caption)))

                                # No thumbnail exists, add as a link in a list
                                else:
                                    obj_links.append(OBJECTS_LINK.format(
                                        path=file_relpath, label='{}: Click to see full-size figure'.format(caption)))

                            else:
                                warnings.append(caption)
                    else:
                        _LOGGER.debug("No custom summarizers were found for this pipeline. Proceeded with default only.")
                if warnings:
                    _LOGGER.warning("Summarizer was unable to find: " +
                                 ', '.join(str(file) for file in warnings))

                while num_figures < 3:
                    # Add additional empty columns for clean format
                    obj_figs.append("\t\t\t  <div class='col'>")
                    obj_figs.append("\t\t\t  </div>")
                    num_figures += 1

                return ("\n".join(["\t\t<h5>Looper project objects</h5>",
                                   "\t\t<div class='container'>",
                                   "\t\t\t<div class='row justify-content-start'>",
                                   "\n".join(obj_figs),
                                   "\t\t\t</div>",
                                   "\t\t</div>",
                                   OBJECTS_LIST_HEADER,
                                   "\n".join(obj_links),
                                   OBJECTS_LIST_FOOTER]))

        def create_index_html(objs, stats, col_names):
            """
            Generate an index.html style project home page w/ sample summary
            statistics

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            """

            reports_dir = get_reports_dir()

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
                table_row_data=[]
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
                    _LOGGER.debug("processing sample: {}".format(sample_name))
                    # Order table_row by col_names
                    sample_stats = OrderedDict(zip(col_names, table_row))
                    table_cell_data=[]
                    for value in table_row:
                        if value == sample_name:
                            # Generate individual sample page and return link
                            sample_page = create_sample_html(objs, stats, sample_name, sample_stats, reports_dir)
                            # Treat sample_name as a link to sample page
                            data = [sample_page, sample_name]
                        # If not the sample name, add as an unlinked cell value
                        else:
                            data = str(value)
                        table_cell_data.append(data)
                        # _LOGGER.debug("table cell: {}".format(table_cell_data))
                    sample_pos += 1
                    table_row_data.append(table_cell_data)
                    # _LOGGER.debug("table row: {}".format(table_row_data))
            else:
                _LOGGER.warning("No stats file '%s'", tsv_outfile_path)

            # Create parent samples page with links to each sample
            save_html(os.path.join(reports_dir, "samples.html"), create_sample_parent_html(objs, stats, reports_dir))

            # Create objects pages
            if not objs.dropna().empty:
                for key in objs['key'].drop_duplicates().sort_values():
                    single_object = objs[objs['key'] == key]
                    create_object_html(single_object, objs, stats, reports_dir)

            # Create parent objects page with links to each object type
            save_html(os.path.join(reports_dir, "objects.html"), create_object_parent_html(objs, stats, reports_dir))
            # Create status page with each sample's status listed
            save_html(os.path.join(reports_dir, "status.html"), create_status_html(objs, stats, reports_dir))
            # Add project level objects
            project_objects = create_project_objects()
            # Complete and close HTML file

            template_vars = dict(project_name=self.prj.name, navbar=create_navbar(objs, stats, self.prj.metadata.output_dir), stats_file_path=stats_file_path, project_objects=project_objects, columns=col_names, table_row_data=table_row_data, version=v)
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


def get_flags(sample_dir):
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


def uniqify(seq):
    """ Fast way to uniqify while preserving input order. """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


