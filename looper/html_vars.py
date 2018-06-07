""" Html constants """

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"

# Generic 
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
        <link rel="stylesheet" href="https://bootswatch.com/4/flatly/bootstrap.min.css">
"""
HTML_TITLE = \
"""\
        <title>PEPATAC project summary for {project_name}</title>
"""
NAVBAR_HEADER = \
"""\
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
          <a class="navbar-brand" href="#">PEPATAC</a>
          <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>

          <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav mr-auto">
              <li class="nav-item active">
                <a class="nav-link" href="{index_html}">Home <span class="sr-only">(current)</span></a>
              </li>
"""
NAVBAR_DROPDOWN_HEADER = \
"""\
              <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                  {menu_name}
                </a>
                <div class="dropdown-menu" aria-labelledby="navbarDropdown">
"""
NAVBAR_DROPDOWN_LINK = \
"""\
                  <a class="dropdown-item" href="{html_page}">{page_name}</a>
"""
NAVBAR_DROPDOWN_FOOTER = \
"""\
                </div>
              </li>
"""
NAVBAR_FOOTER = \
"""\
            </ul>
            <form class="form-inline my-2 my-lg-0">
              <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search">
              <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
            </form>
          </div>
        </nav>
"""
HTML_NAVBAR_STYLE_BASIC = \
"""\
    <style>
        ul.navbar {
            list-style-type: none;
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #333333;
        }

        li.navbar {
            float: left;
        }

        li.navbar a {
            display: block;
            color: white;
            text-align: center;
            padding: 16px;
            text-decoration: none;
        }

        li.navbar a:hover {
            background-color: #111111;
        }
    </style>
"""
HTML_NAVBAR_BASIC = \
"""\
    <ul class="navbar">
        <li class="navbar"><a href='{index_html}'>Home</a></li>
        <li class="navbar"><a href='{objects_html}'>Objects</a></li>
        <li class="navbar"><a href='{samples_html}'>Samples</a></li>
    </ul>
"""
HTML_HEAD_CLOSE = \
"""\
    </head>
    <body>
"""
HTML_FOOTER = \
"""\
        <!-- Optional JavaScript -->
        <!-- jQuery first, then Popper.js, then Bootstrap JS -->
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
    </body>
</html>
"""

GENERIC_LIST_HEADER = \
"""\
<h3>Click to see each object type for all samples</h3>
    <ul style="list-style-type:circle">
"""

GENERIC_LIST_ENTRY = \
"""\
        <li><a href='{object_page}'>{object_type}</a></li>
"""

GENERIC_LIST_FOOTER = \
"""
    </ul> 
"""

NAVBAR_VARS = ["HTML_NAVBAR_STYLE_BASIC", "HTML_NAVBAR_BASIC", "NAVBAR_HEADER",
               "NAVBAR_DROPDOWN_HEADER", "NAVBAR_DROPDOWN_LINK",
               "NAVBAR_DROPDOWN_FOOTER", "NAVBAR_FOOTER"]

GENERIC_VARS = ["HTML_HEAD_OPEN", "HTML_TITLE", "HTML_HEAD_CLOSE",
                "HTML_FOOTER", "GENERIC_LIST_HEADER", "GENERIC_LIST_ENTRY",
                "GENERIC_LIST_FOOTER"]

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
<h3>PEPATAC stats summary</h3>

<div class="table-responsive">
  <table class="table table-hover">                           
    <thead>
        <tr class="stats-firstrow">
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
        <tr>
"""


TABLE_ROWS = \
"""\
            <td>{row_val}</td>
"""

TABLE_FOOTER = \
"""\
        </tr>
    </tbody>
</table>
"""

TABLE_ROWS_LINK = \
"""\
            <td style="cursor:pointer" onclick="location.href='{html_page}'"><a class="LN1 LN2 LN3 LN4 LN5" href="{page_name}" target="_top">{link_name}</a></td>
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
TABLE_VARS = ["TABLE_STYLE_BASIC", "TABLE_HEADER", "TABLE_COLS",
              "TABLE_COLS_FOOTER", "TABLE_ROWS", "TABLE_FOOTER",
              "TABLE_ROWS_LINK", "LINKS_STYLE_BASIC"]

# Sample-page-related
SAMPLE_HEADER = \
"""\
<html>
<h1>{sample_name} figures</h1>
    <body>
        <p><a href='{index_html_path}'>Return to summary page</a></p>

"""

SAMPLE_PLOTS = \
"""\
        <p><a href='{path}'><img src='{image}'><br>{label}</a></p>
"""

SAMPLE_FOOTER = \
"""
        <p><a href='{index_html_path}'>Return to summary page</a></p>
    </body>
</html>
"""
SAMPLE_VARS = ["SAMPLE_HEADER", "SAMPLE_PLOTS", "SAMPLE_FOOTER"]

# Objects-page-related
OBJECTS_HEADER = \
"""\
<html>
<h1>{object_type} figures</h1>
    <body>
        <p><a href='{index_html_path}'>Return to summary page</a></p>

"""

OBJECTS_LINK = \
"""\
<p><a href='{object_page}'>View {object_type} for each sample</a></p>
"""

OBJECTS_PLOTS = \
"""\
        <p><a href='{path}'><img src='{image}'>{label}</a></p>
"""

OBJECTS_FOOTER = \
"""
        <p><a href='{index_html_path}'>Return to summary page</a></p>
    </body>
</html>
"""
OBJECTS_VARS = ["OBJECTS_HEADER", "OBJECTS_LINK", "OBJECTS_PLOTS",
                "OBJECTS_FOOTER"]

__all__ = GENERIC_VARS + NAVBAR_VARS + TABLE_VARS + SAMPLE_VARS + OBJECTS_VARS