""" Html constants """

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"

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
        <link rel="stylesheet" href="https://bootswatch.com/4/flatly/bootstrap.min.css">
"""
HTML_TITLE = \
"""\
        <title>PEPATAC project summary for {project_name}</title>
"""
HTML_HEAD_CLOSE = \
"""\
    </head>
    <body>
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
          <a class="navbar-brand" href="#top">PEPATAC</a>
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

NAVBAR_VARS = ["HTML_NAVBAR_STYLE_BASIC", "HTML_NAVBAR_BASIC", "NAVBAR_HEADER",
               "NAVBAR_DROPDOWN_HEADER", "NAVBAR_DROPDOWN_LINK",
               "NAVBAR_DROPDOWN_DIVIDER", "NAVBAR_DROPDOWN_FOOTER",
               "NAVBAR_MENU_LINK", "NAVBAR_SEARCH_FOOTER", "NAVBAR_FOOTER"]

# Generic HTML vars
GENERIC_LIST_HEADER = \
"""\
<h3>Click to see each object type for all samples</h3>
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
TABLE_STYLE_ROTATED_HEADER = \
"""\
        <style>
        .table-header-rotated th.row-header{
          width: auto;
        }
        .table-header-rotated td{
          width: 60px;
          <!-- border-top: 1px solid #dddddd; -->
          border-left: 1px solid #dddddd;
          border-right: 1px solid #dddddd;
          vertical-align: middle;
          text-align: center;
        }
        .table-header-rotated th.rotate-45{
          height: 120px;
          width: 60px;
          min-width: 60px;
          max-width: 60px;
          position: relative;
          vertical-align: bottom;
          padding: 0;
          font-size: 14px;
          line-height: 0.8;
        }
        .table-header-rotated th.rotate-45 > div{
          position: relative;
          top: 0px;
          left: 60px; /* 120 * tan(45) / 2 = 40 where 120 is the height on the cell and 45 is the transform angle*/
          height: 100%;
          -ms-transform:skew(-45deg,0deg);
          -moz-transform:skew(-45deg,0deg);
          -webkit-transform:skew(-45deg,0deg);
          -o-transform:skew(-45deg,0deg);
          transform:skew(-45deg,0deg);
          overflow: hidden;
          border-left: 1px solid #dddddd;
          border-right: 1px solid #dddddd;
          <!-- border-top: 1px solid #dddddd; -->
        }
        .table-header-rotated th.rotate-45 span {
          -ms-transform:skew(45deg,0deg) rotate(315deg);
          -moz-transform:skew(45deg,0deg) rotate(315deg);
          -webkit-transform:skew(45deg,0deg) rotate(315deg);
          -o-transform:skew(45deg,0deg) rotate(315deg);
          transform:skew(45deg,0deg) rotate(315deg);
          position: absolute;
          bottom: 30px; /* 60 cos(45) = 28 with an additional 2px margin*/
          left: -25px; /*Because it looked good, but there is probably a mathematical link here as well*/
          display: inline-block;
          // width: 100%;
          width: 85px; /* 120 / cos(45) - 60 cos (45) = 85 where 120 is the height of the cell, 60 the width of the cell and 45 the transform angle*/
          text-align: left;
          // white-space: nowrap; /*whether to display in one line or not*/
        }
        
        .table td.text {
            max-width: 150px;
        }
        .table td.text span {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: inline-block;
            max-width: 100%;
        }
        .table td.text span:active {
            white-space: normal;
            text-overflow: clip;
            max-width: 100%;
        }
        </style>
"""
TABLE_HEADER = \
"""
      <h5>PEPATAC stats summary</h5>

      <div class="table-responsive-sm">
        <table class="table table-hover table-header-rotated">                           
          <thead>
            <tr class="stats-firstrow">
"""

TABLE_COLS = \
"""\
              <th class="rotate-45"><div><span>{col_val}</span></div></th>
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
              <td class="text"><span>{row_val}</span></td>
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
              "TABLE_COLS_FOOTER", "TABLE_ROW_HEADER", "TABLE_ROWS",
              "TABLE_ROW_FOOTER", "TABLE_FOOTER",
              "TABLE_ROWS_LINK", "LINKS_STYLE_BASIC",
              "TABLE_STYLE_ROTATED_HEADER"]

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
SAMPLE_VARS = ["SAMPLE_HEADER", "SAMPLE_BUTTONS",
               "SAMPLE_PLOTS", "SAMPLE_FOOTER"]

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
            <table class="table table-hover table-bordered">
              <thead>
                <th>Sample name</th>
                <th>Status</th>
                <th>Log file</th>
                <th>Runtime</th>
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
            <li class="list-group-item"><a href='{path}'>'{label}'</a></li>\
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