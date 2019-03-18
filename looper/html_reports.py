""" Generate HTML reports """

import os
import glob
import pandas as _pd
import logging
import jinja2

from collections import OrderedDict

_LOGGER = logging.getLogger('HTMLReportBuilder')

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"

TEMPLATES_DIRNAME = "jinja_templates"
NAVBAR_LOGO = \
"""\
data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhLS0gQ3JlYXRlZCB3aXRoIElua3NjYXBlIChodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy8pIC0tPgoKPHN2ZwogICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgIHhtbG5zOmNjPSJodHRwOi8vY3JlYXRpdmVjb21tb25zLm9yZy9ucyMiCiAgIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJjZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB3aWR0aD0iNjMuODg1MTM2bW0iCiAgIGhlaWdodD0iNTguNTA0NzA3bW0iCiAgIHZpZXdCb3g9IjAgMCAyMjYuMzY0NjUgMjA3LjMwMDEzIgogICBpZD0ic3ZnNDE5OCIKICAgdmVyc2lvbj0iMS4xIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkxIHIxMzcyNSIKICAgc29kaXBvZGk6ZG9jbmFtZT0ibG9nb19sb29wZXIuc3ZnIj4KICA8ZGVmcwogICAgIGlkPSJkZWZzNDIwMCIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgaWQ9ImJhc2UiCiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEuMCIKICAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgIGlua3NjYXBlOnBhZ2VzaGFkb3c9IjIiCiAgICAgaW5rc2NhcGU6em9vbT0iMi44Mjg0MjcxIgogICAgIGlua3NjYXBlOmN4PSI4MC45NTQ1MzIiCiAgICAgaW5rc2NhcGU6Y3k9IjIyOS42MjgxOCIKICAgICBpbmtzY2FwZTpkb2N1bWVudC11bml0cz0icHgiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ibGF5ZXIxIgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBmaXQtbWFyZ2luLXRvcD0iMiIKICAgICBmaXQtbWFyZ2luLWxlZnQ9IjMiCiAgICAgZml0LW1hcmdpbi1yaWdodD0iMyIKICAgICBmaXQtbWFyZ2luLWJvdHRvbT0iMiIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGE0MjAzIj4KICAgIDxyZGY6UkRGPgogICAgICA8Y2M6V29yawogICAgICAgICByZGY6YWJvdXQ9IiI+CiAgICAgICAgPGRjOmZvcm1hdD5pbWFnZS9zdmcreG1sPC9kYzpmb3JtYXQ+CiAgICAgICAgPGRjOnR5cGUKICAgICAgICAgICByZGY6cmVzb3VyY2U9Imh0dHA6Ly9wdXJsLm9yZy9kYy9kY21pdHlwZS9TdGlsbEltYWdlIiAvPgogICAgICAgIDxkYzp0aXRsZT48L2RjOnRpdGxlPgogICAgICA8L2NjOldvcms+CiAgICA8L3JkZjpSREY+CiAgPC9tZXRhZGF0YT4KICA8ZwogICAgIGlua3NjYXBlOmxhYmVsPSJMYXllciAxIgogICAgIGlua3NjYXBlOmdyb3VwbW9kZT0ibGF5ZXIiCiAgICAgaWQ9ImxheWVyMSIKICAgICB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMjc4LjI0NjI0LC04NTQuNDI2NDIpIj4KICAgIDxwYXRoCiAgICAgICBzdHlsZT0iZmlsbDojNWY4ZGQzO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmUiCiAgICAgICBpZD0icGF0aDQxNDYiCiAgICAgICBkPSJtIDM0NS40MjUyNCw5OTMuMDc5MDQgYyA2LjE1MSwwIDEyLjQwOCwtMS4wMTQgMTguNTM2LC0zLjE0NyBsIC00LjYwOCwtMTMuMjIxIGMgLTIyLjEyNiw3LjcwMyAtNDYuMzk5LC00LjAyMSAtNTQuMTA1LC0yNi4xNCAtNy43MTEsLTIyLjEyMDAxIDQuMDE1LC00Ni4zOTEwMSAyNi4xMzcsLTU0LjEwMzAxIDguMzI3LC0yLjkwMiAxNy4xNzcsLTMuMTM1IDI1LjUxMywtMC43NyBsIC0xNS4yNiw4LjA4MyA2LjU1NCwxMi4zNzIgMzYuNTQ4MDEsLTE5LjM2IC0yMi4yMDMwMSwtMzUuMjggLTExLjg0OSw3LjQ1NiA4LjAwMywxMi43MTkgYyAtMTAuNDg3LC0yLjU2MyAtMjEuNTA5LC0yLjA2NCAtMzEuOTE1LDEuNTYyIC0yOS40MTIsMTAuMjUzIC00NS4wMDAwMSw0Mi41MjEgLTM0Ljc0OTAxLDcxLjkzMDAxIDguMTEyMDEsMjMuMjggMzAuMDIyMDEsMzcuODk5IDUzLjM5ODAxLDM3Ljg5OSB6IgogICAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIKICAgICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0ic2NjY2NjY2NjY2NjY2NzIiAvPgogICAgPHJlY3QKICAgICAgIHN0eWxlPSJjb2xvcjojMDAwMDAwO2NsaXAtcnVsZTpub256ZXJvO2Rpc3BsYXk6aW5saW5lO292ZXJmbG93OnZpc2libGU7dmlzaWJpbGl0eTp2aXNpYmxlO29wYWNpdHk6MTtpc29sYXRpb246YXV0bzttaXgtYmxlbmQtbW9kZTpub3JtYWw7Y29sb3ItaW50ZXJwb2xhdGlvbjpzUkdCO2NvbG9yLWludGVycG9sYXRpb24tZmlsdGVyczpsaW5lYXJSR0I7c29saWQtY29sb3I6IzAwMDAwMDtzb2xpZC1vcGFjaXR5OjE7ZmlsbDojNWY4ZGQzO2ZpbGwtb3BhY2l0eToxO2ZpbGwtcnVsZTpub256ZXJvO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLWxpbmVjYXA6YnV0dDtzdHJva2UtbGluZWpvaW46bWl0ZXI7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmU7c3Ryb2tlLWRhc2hvZmZzZXQ6MDtzdHJva2Utb3BhY2l0eToxO21hcmtlcjpub25lO2NvbG9yLXJlbmRlcmluZzphdXRvO2ltYWdlLXJlbmRlcmluZzphdXRvO3NoYXBlLXJlbmRlcmluZzphdXRvO3RleHQtcmVuZGVyaW5nOmF1dG87ZW5hYmxlLWJhY2tncm91bmQ6YWNjdW11bGF0ZSIKICAgICAgIGlkPSJyZWN0NDE1NyIKICAgICAgIHdpZHRoPSI0NC4wMzc0NDkiCiAgICAgICBoZWlnaHQ9IjExLjAwOTgxMiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgeT0iOTIyLjc4NjMyIiAvPgogICAgPHJlY3QKICAgICAgIHk9IjkzOS41NTQyNiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgaGVpZ2h0PSIxMS4wMDk4MTIiCiAgICAgICB3aWR0aD0iNDQuMDM3NDQ5IgogICAgICAgaWQ9InJlY3Q0MTU5IgogICAgICAgc3R5bGU9ImNvbG9yOiMwMDAwMDA7Y2xpcC1ydWxlOm5vbnplcm87ZGlzcGxheTppbmxpbmU7b3ZlcmZsb3c6dmlzaWJsZTt2aXNpYmlsaXR5OnZpc2libGU7b3BhY2l0eToxO2lzb2xhdGlvbjphdXRvO21peC1ibGVuZC1tb2RlOm5vcm1hbDtjb2xvci1pbnRlcnBvbGF0aW9uOnNSR0I7Y29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzOmxpbmVhclJHQjtzb2xpZC1jb2xvcjojMDAwMDAwO3NvbGlkLW9wYWNpdHk6MTtmaWxsOiM1ZjhkZDM7ZmlsbC1vcGFjaXR5OjE7ZmlsbC1ydWxlOm5vbnplcm87c3Ryb2tlOiNmZmZmZmY7c3Ryb2tlLXdpZHRoOjEuNTtzdHJva2UtbGluZWNhcDpidXR0O3N0cm9rZS1saW5lam9pbjptaXRlcjtzdHJva2UtbWl0ZXJsaW1pdDo0O3N0cm9rZS1kYXNoYXJyYXk6bm9uZTtzdHJva2UtZGFzaG9mZnNldDowO3N0cm9rZS1vcGFjaXR5OjE7bWFya2VyOm5vbmU7Y29sb3ItcmVuZGVyaW5nOmF1dG87aW1hZ2UtcmVuZGVyaW5nOmF1dG87c2hhcGUtcmVuZGVyaW5nOmF1dG87dGV4dC1yZW5kZXJpbmc6YXV0bztlbmFibGUtYmFja2dyb3VuZDphY2N1bXVsYXRlIiAvPgogICAgPHJlY3QKICAgICAgIHN0eWxlPSJjb2xvcjojMDAwMDAwO2NsaXAtcnVsZTpub256ZXJvO2Rpc3BsYXk6aW5saW5lO292ZXJmbG93OnZpc2libGU7dmlzaWJpbGl0eTp2aXNpYmxlO29wYWNpdHk6MTtpc29sYXRpb246YXV0bzttaXgtYmxlbmQtbW9kZTpub3JtYWw7Y29sb3ItaW50ZXJwb2xhdGlvbjpzUkdCO2NvbG9yLWludGVycG9sYXRpb24tZmlsdGVyczpsaW5lYXJSR0I7c29saWQtY29sb3I6IzAwMDAwMDtzb2xpZC1vcGFjaXR5OjE7ZmlsbDojNWY4ZGQzO2ZpbGwtb3BhY2l0eToxO2ZpbGwtcnVsZTpub256ZXJvO3N0cm9rZTojZmZmZmZmO3N0cm9rZS13aWR0aDoxLjU7c3Ryb2tlLWxpbmVjYXA6YnV0dDtzdHJva2UtbGluZWpvaW46bWl0ZXI7c3Ryb2tlLW1pdGVybGltaXQ6NDtzdHJva2UtZGFzaGFycmF5Om5vbmU7c3Ryb2tlLWRhc2hvZmZzZXQ6MDtzdHJva2Utb3BhY2l0eToxO21hcmtlcjpub25lO2NvbG9yLXJlbmRlcmluZzphdXRvO2ltYWdlLXJlbmRlcmluZzphdXRvO3NoYXBlLXJlbmRlcmluZzphdXRvO3RleHQtcmVuZGVyaW5nOmF1dG87ZW5hYmxlLWJhY2tncm91bmQ6YWNjdW11bGF0ZSIKICAgICAgIGlkPSJyZWN0NDE2MSIKICAgICAgIHdpZHRoPSI0NC4wMzc0NDkiCiAgICAgICBoZWlnaHQ9IjExLjAwOTgxMiIKICAgICAgIHg9IjMyNC4xMTgxIgogICAgICAgeT0iOTU2LjMyMjIiIC8+CiAgICA8cGF0aAogICAgICAgc3R5bGU9ImZpbGw6IzVmOGRkMztzdHJva2U6I2ZmZmZmZjtzdHJva2Utd2lkdGg6MS41O3N0cm9rZS1taXRlcmxpbWl0OjQ7c3Ryb2tlLWRhc2hhcnJheTpub25lIgogICAgICAgaWQ9InBhdGg0MTY3IgogICAgICAgZD0ibSA0OTIuMDAzODQsMTAzMi41MjM2IGMgLTQuMDAwMjYsLTguNjkwMiAtOC45MjAxMSwtMjIuODA2MSAtOS43MDE3NywtMzMuOTMzMjMgbCAtMC41MDU3OCwtNy4wODA5MSAtNy44NjI1OCwxNi43ODI2NCAtMTcuMTA0NTQsLTE3LjEwNDUgOS4wODA5MSwwIGMgNi41NzUxNCwwIDExLjk1NDc5LC01LjM3OTY2IDExLjk1NDc5LC0xMS45NTQ3OSBsIDAsLTU5LjYxNDQ0IGMgMCwtNi41NzUxMyAtNS4zNzk2NSwtMTEuOTU0NzkgLTExLjk1NDc5LC0xMS45NTQ3OSBsIC03Ni45Mjg4NCwwIGMgLTYuNTc1MTMsMCAtMTEuOTU0NzksNS4zNzk2NiAtMTEuOTU0NzksMTEuOTU0NzkgbCAwLDU5LjYxNDQ0IGMgMCw2LjU3NTEzIDUuMzc5NjYsMTEuOTU0NzkgMTEuOTU0NzksMTEuOTU0NzkgbCAzLjMxMDU2LDAgLTE3LjEwNDU0LDE3LjEwNDUgLTcuODYyNTgsLTE2Ljc4MjY0IC0wLjUwNTc4LDcuMDgwOTEgYyAtMC43ODE2NiwxMS4xMjcxMyAtNS43MDE1MiwyNS4yNDMwMyAtOS43MDE3NywzMy45MzMyMyBsIC0yLjA2OTEsNC41MDYgNC41MDYwNCwtMi4wNjkxIGMgOC42OTAyMSwtNC4wMDAyIDIyLjgwNjA2LC04LjkyMDEgMzMuOTMzMjEsLTkuNzAxNyBsIDcuMDgwOTEsLTAuNTA1OCAtMTYuNzgyNjgsLTcuODYyNiAyNS4yNDMsLTI1LjI0MyBjIDAuMTM3OTQsLTAuMTM3OTQgMC4yNzU4OCwtMC4zMjE4NiAwLjQxMzgyLC0wLjUwNTc4IGwgOS4xNTIzMiwwIDAsMjguOTY3MzggLTE3LjQyNjQsLTYuMjk5MyA0LjY4OTk1LDUuMzMzNyBjIDcuMzEwODIsOC40MTQzIDEzLjc5Mzk5LDIxLjg0MDUgMTcuMTUwNTMsMzAuODUyNiBsIDEuNzQ3MjQsNC42NDM5IDEuNzAxMjYsLTQuNjQzOSBjIDMuMzEwNTUsLTguOTY2MSA5Ljc5MzczLC0yMi40MzgzIDE3LjE1MDUyLC0zMC44NTI2IGwgNC42ODk5NiwtNS4zMzM3IC0xNy40MjY0MSw2LjI5OTMgMCwtMjguOTY3MzggOC43MTUzOCwwIGMgMC4xMzc5NCwwLjE4MzkyIDAuMjc1ODgsMC4zMjE4NiAwLjQxMzgyLDAuNTA1NzggbCAyNS4yNDMsMjUuMjQzIC0xNi43ODI2OSw3Ljg2MjYgNy4wODA5MiwwLjUwNTggYyAxMS4xMjcxNSwwLjc4MTYgMjUuMjQzLDUuNzAxNSAzMy45MzMyMSw5LjcwMTcgbCA0LjUwNjA0LDIuMDY5MSB6IG0gLTEwMi4xMDMsLTExMS45ODU2MyA3NS4xMzU2MiwwIDAsNTcuNzc1MjQgLTc1LjEzNTYyLDAgeiIKICAgICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiCiAgICAgICBzb2RpcG9kaTpub2RldHlwZXM9ImNjY2Njc3Nzc3Nzc3NjY2NjY2NjY2Njc2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2MiIC8+CiAgPC9nPgo8L3N2Zz4K\
"""

# HTML generator vars
HTML_HEAD_OPEN = \
"""\
<!doctype html>
<html lang="en">
    <head>
        <!-- Required meta tags -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <!-- Bootstrap CSS 
        /*!
         * Bootswatch v4.1.1
         * Homepage: https://bootswatch.com
         * Copyright 2012-2018 Thomas Park
         * Licensed under MIT
         * Based on Bootstrap
        *//*!
         * Bootstrap v4.1.1 (https://getbootstrap.com/)
         * Copyright 2011-2018 The Bootstrap Authors
         * Copyright 2011-2018 Twitter, Inc.
         * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
         -->
        <link rel="stylesheet" href="https://cdn.datatables.net/1.10.18/css/jquery.dataTables.min.css">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css">
"""
HTML_TITLE = \
"""\
        <title>Looper: {project_name} summary</title>
"""
HTML_HEAD_CLOSE = \
"""\
    </head>
    <body>
      <div class="container">
"""
HTML_BUTTON = \
"""\
	  <hr>
	  <div class='container-fluid'>
		  <p class='text-left'>
		  <a class='btn btn-info' href='{file_path}' role='button'>{label}</a>
		  </p>
	  </div>
	  <hr>
"""
HTML_FIGURE = \
"""\
              <div class="col">
                <figure class="figure">
                  <a href='{path}'><img style="width: 100%; height: 100%" src='{image}' class="figure-img img-fluid rounded img-thumbnail" alt=""></a>
                  <a href='{path}'><figcaption class="figure-caption text-left">'{label}'</figcaption></a>
                </figure>
              </div>\
"""
HTML_FOOTER = \
"""\
        <!-- Optional JavaScript -->
        <!-- jQuery first, then Popper.js, then Bootstrap JS -->
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>

        <!-- D3.js -->
        <script src="https://d3js.org/d3.v5.min.js"></script>
        <!-- Plotly -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

        <!-- DataTables JQuery extension -->
        <script src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/fixedcolumns/3.2.6/js/dataTables.fixedColumns.min.js"></script>
        <script src="https://cdn.datatables.net/responsive/2.2.3/js/dataTables.responsive.min.js"></script>

        <script type="text/javascript">
          /* 
          modified DataTable plug-in from https://datatables.net/blog/2016-02-26
          to include comma inserter regex from StackOverflow https://stackoverflow.com/questions/2901102/how-to-print-a-number-with-commas-as-thousands-separators-in-javascript
          */
          $.fn.dataTable.render.ellipsis = function ( cutoff, wordbreak, escapeHtml ) {
              var esc = function ( t ) {
                  return t
                      .replace( /&/g, '&amp;' )
                      .replace( /</g, '&lt;' )
                      .replace( />/g, '&gt;' )
                      .replace( /"/g, '&quot;' );
              };
              function numberWithCommas(x) {
                  var parts = x.toString().split(".");
                  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                  return parts.join(".");
              }
              return function ( d, type, row ) {
                  // Order, search and type get the original data
                  if ( type !== 'display' ) {
                      return d;
                  }
                  if ( typeof d !== 'number' && typeof d !== 'string' ) {
                      return d;
                  }
                  d = d.toString(); // cast numbers
                  if(!isNaN(d)){
                      return numberWithCommas(d);
                  }
                  if ( d.length < cutoff ) {
                      return d;
                  }
                  var shortened = d.substr(0, cutoff-1);
                  // Find the last white space character in the string
                  if ( wordbreak ) {
                      shortened = shortened.replace(/\s([^\s]*)$/, '');
                  }
                  // Protect against uncontrolled HTML input
                  if ( escapeHtml ) {
                      shortened = esc( shortened );
                  }
                  return '<span class="ellipsis" title="'+esc(d)+'">'+shortened+'&#8230;</span>';
              };
          };

          $(document).ready(function() {
            $('#data-table').DataTable({
              scrollX: true,
              fixedColumns: {
                leftColumns: 1
              },
              columnDefs: [ 
                {
                  targets: 0,
                  render: $.fn.dataTable.render.ellipsis(1000, true)
                },
                {
                  targets: '_all',
                  render: $.fn.dataTable.render.ellipsis(17, true)
                }
              ],
            });
          } );

          var table = document.getElementById("data-table");

          function graphCol(colname){
            /* Creates a graph using Plotly.js */
            categories = getX();
            Ydata = getY(colname);

            var data = [{
              x: categories,
              y: Ydata,
              type: 'bar',
            }];

            var layout = {
              title: colname
            };
            chart = document.getElementById('charts');
            Plotly.newPlot(chart, data, layout);
          }
          function getX(){
            /* Get the sample names (the x values in the bar chart) */
            var rows = [];
            for(var i = 1, row; row = table.rows[i]; i++){
              rows.push(row.cells[0].textContent);
            }
            return rows;
          }
          function getY(colname){
            /* Gets the data in the specified column name (the y values in the bar chart) */
            var data = [];
            var colnum;
            // find which column number is the one matching the column name
            for(var i = 0; i < table.rows[0].cells.length; i++){
              if(table.rows[0].cells[i].textContent == colname){
                colnum = i;
                break;
              }
            }
            // add the data from the column to an array
            for(var i = 1, row; row = table.rows[i]; i++){
              data.push(row.cells[colnum].textContent);
            }
            return data;
          }

          function columnClicked(colname){
            /* The function that is called when a column's header is clicked */
            graphCol(colname);
          }

          function modifyNumericColumns(){
            /* Changes a column's header if the data is visualizable */

            var table = document.getElementById("data-table");
            for(var i = 0; i < table.rows[1].cells.length; i++) {  
                //iterate through first row, which will show if a column's data is numeric
                if(!isNaN(table.rows[1].cells[i].textContent)){
                  element = table.rows[0].cells[i]
                  text = element.textContent;
                  $("#plot-cols").append("<li><a href='#' title='Click to visualize this column' onclick='columnClicked(\\""+text+"\\");return false;'>" + text + "</a></li>");
                }
            }
          }
          modifyNumericColumns();
          </script>
      </div>
    </body>
</html>
"""
HTML_VARS = ["HTML_HEAD_OPEN", "HTML_TITLE", "HTML_HEAD_CLOSE",
             "HTML_BUTTON", "HTML_FIGURE", "HTML_FOOTER"]

# Navigation-related vars
NAVBAR_HEADER = \
"""\
        <div id="top"></div>
        <nav class="navbar sticky-top navbar-expand-lg navbar-dark bg-primary">
          <a class="navbar-left" href="#top"><img src="{logo}" class="d-inline-block align-middle img-responsive" alt="LOOPER" style="max-height:60px; margin-top:-10px; margin-bottom:-10px"></a>
          <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav mr-auto">
              <li class="nav-item active">
                <a class="nav-link" href="{index_html}">Summary<span class="sr-only">(current)</span></a>
              </li>\
"""

NAVBAR_DROPDOWN_HEADER = \
"""\
              <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                  {menu_name}
                </a>
                <div class="dropdown-menu" aria-labelledby="navbarDropdown">\
"""
NAVBAR_DROPDOWN_DIVIDER = \
"""\
                  <div class="dropdown-divider"></div>\
"""
NAVBAR_DROPDOWN_LINK = \
"""\
                  <a class="dropdown-item" href="{html_page}">{page_name}</a>\
"""
NAVBAR_DROPDOWN_FOOTER = \
"""\
                </div>
              </li>\
"""
NAVBAR_MENU_LINK = \
"""\
              <li class="nav-item">
                <a class="nav-link" href="{html_page}">{page_name}</a>
              </li>\
"""
NAVBAR_SEARCH_FOOTER = \
"""\
            </ul>
            <form class="form-inline my-2 my-lg-0">
              <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search">
              <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
            </form>
          </div>
        </nav>
"""
NAVBAR_FOOTER = \
"""\
            </ul>
          </div>
        </nav>
"""
# HTML_NAVBAR_STYLE_BASIC = \
# """\
#     <style>
#         ul.navbar {
#             list-style-type: none;
#             margin: 0;
#             padding: 0;
#             overflow: hidden;
#             background-color: #333333;
#         }
#
#         li.navbar {
#             float: left;
#         }
#
#         li.navbar a {
#             display: block;
#             color: white;
#             text-align: center;
#             padding: 16px;
#             text-decoration: none;
#         }
#
#         li.navbar a:hover {
#             background-color: #111111;
#         }
#     </style>
# """
HTML_NAVBAR_BASIC = \
"""\
    <ul class="navbar">
        <li class="navbar"><a href='{index_html}'>Home</a></li>
        <li class="navbar"><a href='{objects_html}'>Objects</a></li>
        <li class="navbar"><a href='{samples_html}'>Samples</a></li>
    </ul>
"""
NAVBAR_VARS = ["HTML_NAVBAR_STYLE_BASIC", "HTML_NAVBAR_BASIC", "NAVBAR_HEADER",
               "NAVBAR_LOGO", "NAVBAR_DROPDOWN_HEADER", "NAVBAR_DROPDOWN_LINK",
               "NAVBAR_DROPDOWN_DIVIDER", "NAVBAR_DROPDOWN_FOOTER",
               "NAVBAR_MENU_LINK", "NAVBAR_SEARCH_FOOTER", "NAVBAR_FOOTER"]

# Generic HTML vars
GENERIC_HEADER = \
"""\
    <h4>{header}</h4>
"""
GENERIC_LIST_HEADER = \
"""\
      <ul style="list-style-type:circle">
"""
GENERIC_LIST_ENTRY = \
"""\
        <li><a href='{page}'>{label}</a></li>
"""
GENERIC_LIST_FOOTER = \
"""
      </ul> 
"""
GENERIC_VARS = ["HTML_HEAD_OPEN", "HTML_TITLE", "HTML_HEAD_CLOSE",
                "HTML_FOOTER", "GENERIC_HEADER", "GENERIC_LIST_HEADER",
                "GENERIC_LIST_ENTRY", "GENERIC_LIST_FOOTER"]

# Table-related
TABLE_STYLE_BASIC = \
"""
        <style type="text/css">
            table.stats-table {
                font-size: 12px;
                border: 1px solid #CCC; 
                font-family: Courier New, Courier, monospace;
            } 
            .stats-table td {
                padding: 4px;
                margin: 3px;
                border: 1px solid #CCC;
            }
            .stats-table th {
                background-color: #104E8B; 
                color: #FFF;
                font-weight: bold;
            }
        </style>
"""
TABLE_HEADER = \
"""
      <div class="row" style="margin-top: 20px; margin-bottom: 20px;">
        <h2 class="col-10">Looper stats summary</h2>
        <button type='button' href='{file_path}' class='btn btn-outline-primary'>{label}</button>
      </div>
      
      <div>
        <table class="display compact" id="data-table">
          <thead>
            <tr>
"""
TABLE_COLS = \
"""\
            <th>{col_val}</th>
"""
TABLE_COLS_FOOTER = \
"""\
            </tr>
          </thead>
          <tbody>
"""
TABLE_ROW_HEADER = \
"""\
            <tr>    
"""
TABLE_ROWS = \
"""\
              <td class="text">{row_val}</td>
"""
TABLE_ROW_FOOTER = \
"""\
            </tr>
"""
TABLE_FOOTER = \
"""\
          </tbody>
        </table>
      </div>
"""
TABLE_ROWS_LINK = \
"""\
              <td style="cursor:pointer" onclick="location.href='{html_page}'"><a class="LN1 LN2 LN3 LN4 LN5" href="{page_name}">{link_name}</a></td>
"""
LINKS_STYLE_BASIC = \
"""
      a.LN1 {
        font-style:normal;
        font-weight:bold;
        font-size:1.0em;
      }

      a.LN2:link {
        color:#A4DCF5;
        text-decoration:none;
      }

      a.LN3:visited {
        color:#A4DCF5;
        text-decoration:none;
      }

      a.LN4:hover {
        color:#A4DCF5;
        text-decoration:none;
      }

      a.LN5:active {
        color:#A4DCF5;
        text-decoration:none;
      }
"""
TABLE_VISUALIZATION = \
"""
      <div class="row">
        <div id="chartableColumns" class="col-3" style="margin: 20px;">
          <h4 style="margin: 20px;">Plottable Columns</h3>
          <ul id="plot-cols">

          </ul>
        </div>
        <div class="col">
          <div id="charts">

          </div>
        </div>
      </div>
"""
TABLE_VARS = ["TABLE_STYLE_BASIC", "TABLE_HEADER", "TABLE_COLS",
              "TABLE_COLS_FOOTER", "TABLE_ROW_HEADER", "TABLE_ROWS",
              "TABLE_ROW_FOOTER", "TABLE_FOOTER",
              "TABLE_ROWS_LINK", "LINKS_STYLE_BASIC", "TABLE_VISUALIZATION"]

# Sample-page-related
SAMPLE_HEADER = \
"""\
<html>
<h1>{sample_name} figures</h1>
    <body>
        <p><a href='{index_html_path}'>Return to summary page</a></p>

"""

SAMPLE_BUTTONS = \
"""\
        <hr>
        <div class="container-fluid">
            <p class="text-left">
            <button type="button" class='{button_class}' disabled>STATUS: {flag}</button>
            <a class="btn btn-info" href='{log_file}' role="button">Log file</a>
            <a class="btn btn-info" href='{profile_file}' role="button">Pipeline profile</a>
            <a class="btn btn-info" href='{commands_file}' role="button">Pipeline commands</a>
            <a class='btn btn-info' href='{stats_file}' role='button'>Stats summary file</a>         
            </p>
        </div>
        <hr>
"""
SAMPLE_TABLE_HEADER = \
"""\
      <h5>Looper stats summary</h5>
        <div class="table-responsive-sm">
          <table class="table table-sm table-hover table-bordered table-condensed" style="white-space: nowrap; width: 1%;">                           
            <tbody>
"""
SAMPLE_TABLE_FIRSTROW = \
"""\
              <tr class="table-light">
                <th>{row_name}</th>
                <td style="cursor:pointer" onclick="location.href='{html_page}'"><a href="{page_name}" target="_top">{link_name}</a></td>
              </tr>
"""
SAMPLE_TABLE_ROW = \
"""\
              <tr>
                <th>{row_name}</th>
                <td class="text"><span>{row_val}</span></td>
              </tr>
"""
SAMPLE_TABLE_STYLE = \
"""\
        .table td.text {
            max-width: 500px;
            padding: 0px 2px 0px 2px;
        }
        .table td.text span {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
            max-width: 100%;
            vertical-align: middle;
        }
        .table td.text span:active {
            white-space: normal;
            text-overflow: clip;
            max-width: 100%;
        }
        .table-condensed > tbody > tr > td,
        .table-condensed > tbody > tr > th {
            padding: 0px 2px 0px 2px;
            vertical-align: middle;
        }
"""
SAMPLE_PLOTS = \
"""\
            <figure class="figure">
                <a href='{path}'><img style="width: 200px; height: 200px" src='{image}' class="figure-img img-fluid rounded" alt=""></a>
                <a href='{path}'><figcaption class="figure-caption text-left">'{label}'</figcaption></a>
            </figure>
"""
SAMPLE_FOOTER = \
"""
        <p><a href='{index_html_path}'>Return to summary page</a></p>
    </body>
</html>
"""
SAMPLE_VARS = ["SAMPLE_HEADER", "SAMPLE_BUTTONS", "SAMPLE_PLOTS",
               "SAMPLE_FOOTER", "SAMPLE_TABLE_HEADER", "SAMPLE_TABLE_STYLE",
               "SAMPLE_TABLE_FIRSTROW", "SAMPLE_TABLE_ROW"]

# Status-page-related
STATUS_HEADER = \
"""\
        <hr>
        <div class="container-fluid">
"""
STATUS_TABLE_HEAD = \
"""\
        <div class="d-flex justify-content-between">
          <div class="table-responsive-sm">
            <table class="table table-sm table-hover table-bordered">
              <thead>
                <th>Sample name</th>
                <th>Status</th>
                <th>Log file</th>
                <th>Runtime</th>
                <th>Peak memory use</th>
              </thead>
              <tbody>
"""
STATUS_BUTTON = \
"""\
                <tr>
                  <td><button type="button" class='{button_class}' disabled>{sample}: {flag}</button></td>
                </tr>
"""
STATUS_ROW_HEADER = \
"""\
                <tr>
"""
STATUS_ROW_VALUE = \
"""\
                  <td class='{row_class}'>{value}</td>
"""
STATUS_ROW_LINK = \
"""\
                  <td class='{row_class}' style="cursor:pointer" onclick="location.href='{file_link}'"><a href="{file_link}" target="_top">{link_name}</a></td>
"""
STATUS_ROW_FOOTER = \
"""\
                </tr>
"""
STATUS_FOOTER = \
"""\
              </tbody>
            </table>
          </div>  
        </div>
        <hr>
"""
STATUS_VARS = ["STATUS_HEADER", "STATUS_TABLE_HEAD", "STATUS_BUTTON",
               "STATUS_ROW_HEADER", "STATUS_ROW_VALUE", "STATUS_ROW_LINK",
               "STATUS_ROW_FOOTER", "STATUS_FOOTER"]

# Objects-page-related
OBJECTS_HEADER = \
"""\
<html>
<h1>{object_type} figures</h1>
    <body>
        <p><a href='{index_html_path}'>Return to summary page</a></p>

"""
OBJECTS_LIST_HEADER = \
"""\
          <ul class="list-group list-group-flush">
"""
OBJECTS_LINK = \
"""\
            <li class="list-group-item" style="padding: 1px 3px 1px 3px;"><a href='{path}'>'{label}'</a></li>\
"""
OBJECTS_LIST_FOOTER = \
"""\
          </ul>
"""
OBJECTS_PLOTS = \
"""\
        <figure class="figure">
          <a href='{path}'><img style="width: 50%; height: 50%" src='{image}' class="figure-img img-fluid rounded" alt=""></a>
          <a href='{path}'><figcaption class="figure-caption text-left">'{label}'</figcaption></a>
        </figure>
"""
OBJECTS_FOOTER = \
"""
        <p><a href='{index_html_path}'>Return to summary page</a></p>
    </body>
</html>
"""
OBJECTS_VARS = ["OBJECTS_HEADER", "OBJECTS_LIST_HEADER", "OBJECTS_LINK",
                "OBJECTS_LIST_FOOTER", "OBJECTS_PLOTS", "OBJECTS_FOOTER"]

__all__ = HTML_VARS + NAVBAR_VARS + GENERIC_VARS + \
          TABLE_VARS + SAMPLE_VARS + STATUS_VARS + OBJECTS_VARS


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
            # TODO: The page is not styled properly, bootstrap missing?
            """
            Generates a page listing all the project objects with links
            to individual object pages

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: path to the reports directory
            """
            reports_dir = get_reports_dir()
            object_parent_path = os.path.join(reports_dir, "objects.html")

            if not os.path.exists(os.path.dirname(object_parent_path)):
                os.makedirs(os.path.dirname(object_parent_path))
            pages = labels = list()
            if not objs.empty:
                for key in objs['key'].drop_duplicates().sort_values():
                    page_name = key + ".html"
                    page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    pages.append(page_relpath)
                    labels.append(key)

            args_dict = dict(navbar=create_navbar(objs, stats, wd), labels=labels, pages=pages, header="Objects")
            return self.render_jinja_template("navbar_list_parent.html", args_dict)

        def create_sample_parent_html(objs, stats, wd):
            """
            Generates a page listing all the project samples with links
            to individual sample pages
            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str wd: path to the working directory
            """
            reports_dir = get_reports_dir()
            sample_parent_path = os.path.join(reports_dir, "samples.html")

            if not os.path.exists(os.path.dirname(sample_parent_path)):
                os.makedirs(os.path.dirname(sample_parent_path))
            pages = labels = list()
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

            args_dict = dict(navbar=create_navbar(objs, stats, wd), labels=labels, pages=pages, header="Samples")
            return self.render_jinja_template("navbar_list_parent.html", args_dict)


        def create_object_html(single_object, all_objects, stats):
            """
            Generates a page for an individual object type with all of its
            plots from each sample
            
            :param panda.DataFrame single_object: contains reference 
                information for an individual object type for all samples
            :param panda.DataFrame all_objects: project level dataframe 
                containing any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            """

            reports_dir = get_reports_dir()

            # Generate object filename
            for key in single_object['key'].drop_duplicates().sort_values():
                type = str(key)
                filename = str(key) + ".html"
            object_path = os.path.join(
                            reports_dir, filename.replace(' ', '_').lower())

            if not os.path.exists(os.path.dirname(object_path)):
                os.makedirs(os.path.dirname(object_path))

            with open(object_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(create_navbar(all_objects, stats, reports_dir))
                html_file.write(HTML_HEAD_CLOSE)
                html_file.write("\t\t<h4>{} objects</h4>\n".format(str(type)))
                links = []
                figures = []
                warnings = []
                for i, row in single_object.iterrows():
                    # Set the PATH to a page for the sample. Catch any errors.
                    try:
                      page_path = os.path.join(
                        self.prj.metadata.results_subdir,
                        row['sample_name'], row['filename'])
                    except AttributeError:
                      err_msg = ("Sample: {} | " +
                                 "Missing valid page path for: {}")
                      # Report the sample that fails, if that information exists
                      if str(row['sample_name']) and str(row['filename']):
                        _LOGGER.warn(err_msg.format(row['sample_name'],
                                                    row['filename']))
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
                        image_path = os.path.join(
                          self.prj.metadata.results_subdir,
                          row['sample_name'], row['anchor_image'])
                      except AttributeError:
                        _LOGGER.warn(str(row))
                        err_msg = ("Sample: {} | " +
                                   "Missing valid image path for: {}")
                        # Report the sample that fails, if that information exists
                        if str(row['sample_name']) and str(row['filename']):
                          _LOGGER.warn(err_msg.format(row['sample_name'],
                                                      row['filename']))
                        else:
                          _LOGGER.warn(err_msg.format("Unknown", "Unknown"))
                        image_path = ""

                    # Check for the presence of both the file and thumbnail
                    if os.path.isfile(image_path) and os.path.isfile(page_path):
                      image_relpath = os.path.relpath(image_path, reports_dir)
                      _LOGGER.debug(str(image_relpath))
                      # If the object has a valid image, use it!
                      if str(image_path).lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
                          figures.append(OBJECTS_PLOTS.format(
                                          path=page_relpath,
                                          image=image_relpath,
                                          label=str(row['sample_name'])))
                      # Or if that "image" is an HTML document
                      elif str(image_path).lower().endswith('.html'):
                        links.append(GENERIC_LIST_ENTRY.format(
                                      page=image_relpath,
                                      label=str(row['sample_name'])))
                      # Otherwise treat as a link
                      elif os.path.isfile(page_path):
                          links.append(GENERIC_LIST_ENTRY.format(
                                        page=page_relpath,
                                        label=str(row['sample_name'])))
                      else:
                          warnings.append(str(row['filename']))
                    # If no thumbnail image is present, add as a link
                    elif os.path.isfile(page_path):
                      links.append(GENERIC_LIST_ENTRY.format(
                                    page=page_relpath,
                                    label=str(row['sample_name'])))
                    else:
                      warnings.append(str(row['filename']))

                html_file.write(GENERIC_LIST_HEADER)
                html_file.write("\n".join(links))
                html_file.write(GENERIC_LIST_FOOTER)
                html_file.write("\t\t\t<hr>\n")
                html_file.write("\n".join(figures))
                html_file.write("\t\t\t<hr>\n")
                html_file.write(HTML_FOOTER)
                html_file.close()

            if warnings:
                _LOGGER.warning("create_object_html: " +
                                filename.replace(' ', '_').lower() +
                                " references nonexistent object files")
                _LOGGER.debug(filename.replace(' ', '_').lower() +
                              " nonexistent files: " +
                              ','.join(str(file) for file in warnings))


        def create_sample_html(objs, stats, sample_name, sample_stats):
            """
            Produce an HTML page containing all of a sample's objects
            and the sample summary statistics

            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample
            :param str sample_name: the name of the current sample
            :param list stats: pipeline run statistics for the current sample
            """

            reports_dir = get_reports_dir()
            html_filename = sample_name + ".html"
            html_page = os.path.join(
                reports_dir, html_filename.replace(' ', '_').lower())
            sample_page_relpath = os.path.relpath(
                html_page, self.prj.metadata.output_dir)

            single_sample = _pd.DataFrame()
            if not objs.empty:
                single_sample = objs[objs['sample_name'] == sample_name]

            if not os.path.exists(os.path.dirname(html_page)):
                os.makedirs(os.path.dirname(html_page))

            with open(html_page, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write("\t\t<style>\n")
                html_file.write(SAMPLE_TABLE_STYLE)
                html_file.write("\t\t</style>\n")
                html_file.write(create_navbar(objs, stats, reports_dir))
                html_file.write(HTML_HEAD_CLOSE)
                html_file.write("\t\t<h4>{}</h4>\n".format(str(sample_name)))
                sample_dir = os.path.join(
                        self.prj.metadata.results_subdir, sample_name)

                # Confirm sample directory exists, then build page
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
                    # Get relative path to the log file
                    log_file = os.path.join(self.prj.metadata.results_subdir,
                                            sample_name, log_name)
                    log_relpath = os.path.relpath(log_file, reports_dir)
                    # Grab the status flag for the current sample
                    flag = glob.glob(os.path.join(self.prj.metadata.results_subdir,
                                                  sample_name, '*.flag'))
                    if not flag:  
                        button_class = "btn btn-danger"
                        flag = "Missing"
                    elif len(flag) > 1:
                        button_class = "btn btn-warning"
                        flag = "Multiple"
                    else:
                        if "completed" in str(flag):
                            button_class = "btn btn-success"
                            flag = "Completed"
                        elif "running" in str(flag):
                            button_class = "btn btn-warning"
                            flag = "Running"
                        elif "failed" in str(flag):
                            button_class = "btn btn-danger"
                            flag = "Failed"
                        else:
                            button_class = "btn btn-secondary"
                            flag = "Unknown"
                    # Create buttons linking the sample's STATUS, LOG, PROFILE,
                    # COMMANDS, and STATS files
                    stats_relpath = os.path.relpath(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, "stats.tsv"), reports_dir)
                    profile_relpath = os.path.relpath(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, profile_name), reports_dir)
                    command_relpath = os.path.relpath(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, command_name), reports_dir)
                    html_file.write(SAMPLE_BUTTONS.format(
                                        button_class=button_class,
                                        flag=flag,
                                        log_file=log_relpath,
                                        profile_file=profile_relpath,
                                        commands_file=command_relpath,
                                        stats_file=stats_relpath))

                    # Add the sample's statistics as a table
                    html_file.write("\t<div class='container-fluid'>\n")
                    html_file.write(SAMPLE_TABLE_HEADER)
                    # Produce table rows
                    for key, value in sample_stats.items():
                        # Treat sample_name as a link to sample page
                        if key == 'sample_name':
                            page_relpath = os.path.relpath(html_page, reports_dir)
                            html_file.write(SAMPLE_TABLE_FIRSTROW.format(
                                                row_name=str(key),
                                                html_page=page_relpath,
                                                page_name=html_filename,
                                                link_name=str(value)))
                        # Otherwise add as a static cell value
                        else:
                            html_file.write(SAMPLE_TABLE_ROW.format(
                                row_name=str(key),
                                row_val=str(value)))

                    html_file.write(TABLE_FOOTER)
                    html_file.write("\t  <hr>\n")
                    # Add all the objects for the current sample
                    html_file.write("\t\t<div class='container-fluid'>\n")
                    html_file.write("\t\t<h5>{sample} objects</h5>\n".format(sample=sample_name))
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
                                        figures.append(SAMPLE_PLOTS.format(
                                                        label=str(row['key']),
                                                        path=page_relpath,
                                                        image=image_relpath))
                                    # Otherwise treat as a link
                                    elif os.path.isfile(page_path):
                                        links.append(GENERIC_LIST_ENTRY.format(
                                                        label=str(row['key']),
                                                        page=page_relpath))
                                    # If neither, there is no object by that name
                                    else:
                                        warnings.append(str(row['filename']))
                                # If no thumbnail image, it's just a link
                                elif os.path.isfile(page_path):
                                    links.append(GENERIC_LIST_ENTRY.format(
                                                    label=str(row['key']),
                                                    page=page_relpath))
                                # If no file present, there is no object by that name
                                else:
                                    warnings.append(str(row['filename']))

                    html_file.write(GENERIC_LIST_HEADER)
                    html_file.write("\n".join(links))
                    html_file.write(GENERIC_LIST_FOOTER)
                    html_file.write("\t\t\t<hr>\n")
                    html_file.write("\n".join(figures))
                    html_file.write("\t\t</div>\n")
                    html_file.write("\t\t<hr>\n")
                    html_file.write(HTML_FOOTER)
                    html_file.close()
                else:
                    # Sample was not run through the pipeline
                    _LOGGER.warning("{} is not present in {}".format(
                        sample_name, self.prj.metadata.results_subdir))
                    html_file.write(HTML_FOOTER)
                    html_file.close()
            # TODO: accumulate warnings from these functions and only display
            #       after all samples are processed
            # _LOGGER.warning("Warning: The following files do not exist: " +
                         # '\t'.join(str(file) for file in warnings))
            # Return the path to the newly created sample page
            return sample_page_relpath


        def create_status_html(objs, stats):
            """
            Generates a page listing all the samples, their run status, their
            log file, and the total runtime if completed.
            
            :param panda.DataFrame objs: project level dataframe containing
                any reported objects for all samples
            :param list stats: a summary file of pipeline statistics for each
                analyzed sample 
            """
            reports_dir = get_reports_dir()
            status_html_path = os.path.join(reports_dir, "status.html")

            if not os.path.exists(os.path.dirname(status_html_path)):
                os.makedirs(os.path.dirname(status_html_path))

            with open(status_html_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write("\t\t<style>th{background-color:white;}</style>\n")
                html_file.write(create_navbar(objs, stats, reports_dir))
                html_file.write(HTML_HEAD_CLOSE)
                html_file.write(STATUS_HEADER)
                html_file.write(STATUS_TABLE_HEAD)

                # Alert user if the stats_summary.tsv is incomplete
                # Likely indicates pipeline is still running
                status_warning = False

                # Alert user to samples that are included in the project
                # but have not been run
                sample_warning = []

                for sample in self.prj.samples:
                    sample_name = str(sample.sample_name)
                    sample_dir = os.path.join(
                            self.prj.metadata.results_subdir, sample_name)

                    # Confirm sample directory exists, then build page
                    if os.path.exists(sample_dir):                        
                        # Grab the status flag for the current sample
                        flag = glob.glob(os.path.join(sample_dir, '*.flag'))               
                        if not flag:
                            button_class = "table-danger"
                            flag = "Missing"
                            _LOGGER.warning("No flag file found for {}".format(sample_name))
                        elif len(flag) > 1:
                            button_class = "table-warning"
                            flag = "Multiple"
                            _LOGGER.warning("Multiple flag files found for {}".format(sample_name))
                        else:
                            if "completed" in str(flag):
                                button_class = "table-success"
                                flag = "Completed"
                            elif "running" in str(flag):
                                button_class = "table-warning"
                                flag = "Running"
                            elif "failed" in str(flag):
                                button_class = "table-danger"
                                flag = "Failed"
                            else:
                                button_class = "table-secondary"
                                flag = "Unknown"

                        # Create table entry for each sample
                        html_file.write(STATUS_ROW_HEADER)
                        # First Col: Sample_Name (w/ link to sample page)
                        page_name = sample_name + ".html"
                        page_path = os.path.join(reports_dir, page_name.replace(' ', '_').lower())
                        page_relpath = os.path.relpath(page_path, reports_dir)
                        html_file.write(STATUS_ROW_LINK.format(
                                            row_class="",
                                            file_link=page_relpath,
                                            link_name=sample_name))
                        # Second Col: Status (color-coded)
                        html_file.write(STATUS_ROW_VALUE.format(
                                            row_class=button_class,
                                            value=flag))
                        # Third Col: Log File (w/ link to file)
                        single_sample = _pd.DataFrame()
                        if not objs.empty:
                            single_sample = objs[objs['sample_name'] == sample_name]
                        if single_sample.empty:
                            # When there is no objects.tsv file, search for the
                            # presence of log, profile, and command files
                            log_name = os.path.basename(str(glob.glob(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, '*log.md'))[0]))
                            # Currently unused. Future?
                            # profile_name = os.path.basename(str(glob.glob(os.path.join(
                                                # self.prj.metadata.results_subdir,
                                                # sample_name, '*profile.tsv'))[0]))
                            # command_name = os.path.basename(str(glob.glob(os.path.join(
                                                # self.prj.metadata.results_subdir,
                                                # sample_name, '*commands.sh'))[0]))
                        else:
                            log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                            # Currently unused. Future?
                            # profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                            # command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
                        log_file = os.path.join(self.prj.metadata.results_subdir,
                                                sample_name, log_name)
                        log_relpath = os.path.relpath(log_file, reports_dir)
                        if os.path.isfile(log_file):
                            html_file.write(STATUS_ROW_LINK.format(
                                                row_class="",
                                                file_link=log_relpath,
                                                link_name=log_name))
                        else:
                            # Leave cell empty
                            html_file.write(STATUS_ROW_LINK.format(
                                                row_class="",
                                                file_link="",
                                                link_name=""))
                        # Fourth Col: Sample runtime (if completed)
                        # Use stats.tsv <deprecated>
                        # * Use log_file instead
                        # stats_file = os.path.join(
                                        # self.prj.metadata.results_subdir,
                                        # sample_name, "stats.tsv")
                        if os.path.isfile(log_file):
                            # t = _pd.read_table(stats_file, header=None,
                                               # names=['key', 'value', 'pl'])
                            # t.drop_duplicates(subset=['key', 'pl'],
                                              # keep='last', inplace=True)
                            # alternate method: better to use log_file?
                            t = _pd.read_table(log_file, header=None,
                                                  names=['key', 'value'])
                            t.drop_duplicates(subset=['value'], keep='last',
                                                 inplace=True)
                            t['key'] = t['key'].str.replace('> `', '')
                            t['key'] = t['key'].str.replace('`', '')
                            try:
                                time = str(t[t['key'] == 'Time'].iloc[0]['value'])
                                html_file.write(STATUS_ROW_VALUE.format(
                                                row_class="",
                                                value=str(time)))
                            except IndexError:
                                status_warning = True                       
                        else:
                            html_file.write(STATUS_ROW_VALUE.format(
                                                row_class=button_class,
                                                value="Unknown"))
                        # Fifth Col: Sample peak memory use (if completed)
                        # Use *_log.md file
                        if os.path.isfile(log_file):
                            m = _pd.read_table(log_file, header=None, sep=':',
                                               names=['key', 'value'])
                            m.drop_duplicates(subset=['value'], keep='last',
                                              inplace=True)
                            m['key'] = m['key'].str.replace('*', '')
                            m['key'] = m['key'].str.replace('^\s+', '')
                            try:
                                mem = str(m[m['key'] == 'Peak memory used'].iloc[0]['value'])
                                html_file.write(STATUS_ROW_VALUE.format(
                                                row_class="",
                                                value=mem.replace(' ', '')))
                            except IndexError:
                                status_warning = True                       
                        else:
                            html_file.write(STATUS_ROW_VALUE.format(
                                                row_class=button_class,
                                                value="NA"))
                        html_file.write(STATUS_ROW_FOOTER)
                    else:
                        # Sample was not run through the pipeline
                        sample_warning.append(sample_name)

                # Close HTML file
                html_file.write(STATUS_FOOTER)
                html_file.write(HTML_FOOTER)
                html_file.close()
                
                # Alert the user to any warnings generated
                if status_warning:
                    _LOGGER.warning("The stats table is incomplete, likely because " +
                                 "one or more jobs either failed or is still running.")
                  
                if sample_warning:
                    if len(sample_warning)==1:
                        _LOGGER.warning("{} is not present in {}".format(
                            ''.join(str(sample) for sample in sample_warning),
                            self.prj.metadata.results_subdir))
                    else:
                        warn_msg = "The following samples are not present in {}: {}"
                        _LOGGER.warning(warn_msg.format(
                            self.prj.metadata.results_subdir,
                            ' '.join(str(sample) for sample in sample_warning)))

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
                                    all_objects=objects_relpath)
            return self.render_jinja_template("my_navbar.html", template_vars)

        def create_project_objects():
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

            index_html_file = open(index_html_path, 'w')
            index_html_file.write(HTML_HEAD_OPEN)
            index_html_file.write("\t\t<style>\n")
            index_html_file.write("\t\t</style>\n")
            index_html_file.write(HTML_TITLE.format(project_name=self.prj.name))
            navbar = create_navbar(objs, stats, self.prj.metadata.output_dir)
            index_html_file.write(navbar)
            index_html_file.write(HTML_HEAD_CLOSE)

            # Add stats_summary.tsv button link
            tsv_outfile_path = os.path.join(self.prj.metadata.output_dir,
                                            self.prj.name)
            if hasattr(self.prj, "subproject") and self.prj.subproject:
                tsv_outfile_path += '_' + self.prj.subproject
            tsv_outfile_path += '_stats_summary.tsv'
            stats_relpath = os.path.relpath(tsv_outfile_path,
                                            self.prj.metadata.output_dir)

            # Add stats summary table to index page and produce individual
            # sample pages
            if os.path.isfile(tsv_outfile_path):
                index_html_file.write(TABLE_HEADER.format(file_path=stats_relpath, label="Stats Summary File"))
                # Produce table columns
                for key in col_names:
                    index_html_file.write(TABLE_COLS.format(col_val=str(key)))
                index_html_file.write(TABLE_COLS_FOOTER)

                # Produce table rows
                sample_pos = 0
                col_pos = 0
                num_columns = len(col_names)
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
                    index_html_file.write(TABLE_ROW_HEADER)
                    # Order table_row by col_names
                    sample_stats = OrderedDict(zip(col_names, table_row))
                    for value in table_row:
                        if value == sample_name:
                            # Generate individual sample page and return link
                            sample_page = create_sample_html(objs,
                                                             stats,
                                                             sample_name,
                                                             sample_stats)
                            # Treat sample_name as a link to sample page
                            index_html_file.write(TABLE_ROWS_LINK.format(
                                html_page=sample_page,
                                page_name=sample_page,
                                link_name=sample_name))
                        # If not the sample name, add as an unlinked cell value
                        else:
                            index_html_file.write(TABLE_ROWS.format(
                                row_val=str(value)))
                    index_html_file.write(TABLE_ROW_FOOTER)
                    sample_pos += 1
                index_html_file.write(TABLE_FOOTER)
                index_html_file.write(TABLE_VISUALIZATION)
            else:
                _LOGGER.warning("No stats file '%s'", tsv_outfile_path)

            # Create parent samples page with links to each sample
            save_html(os.path.join(reports_dir, "samples.html"), create_sample_parent_html(objs, stats, reports_dir))

            # Create objects pages
            if not objs.dropna().empty:
                for key in objs['key'].drop_duplicates().sort_values():
                    single_object = objs[objs['key'] == key]
                    create_object_html(single_object, objs, stats)

            # Create parent objects page with links to each object type
            save_html(os.path.join(reports_dir, "objects.html"), create_object_parent_html(objs, stats, reports_dir))
            # Create status page with each sample's status listed
            create_status_html(objs, stats)

            # Add project level objects
            prj_objs = create_project_objects()
            index_html_file.write("\t\t<hr>\n")
            index_html_file.write(prj_objs)
            index_html_file.write("\t\t<hr>\n")

            # Complete and close HTML file
            index_html_file.write(HTML_FOOTER)
            index_html_file.close()
            
            # Return the path to the completed index.html file
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


def uniqify(seq):
    """ Fast way to uniqify while preserving input order. """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]