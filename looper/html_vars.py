""" Html constants """

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"

# Generic 
HTML_HEADER = \
"""\
<!DOCTYPE html>
<html>
<head>
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
</head>
<body>
"""
HTML_TITLE = \
"""\
<h2>PEPATAC project summary for {project_name}</h2>
"""
HTML_NAVBAR = \
"""\
<ul class="navbar">
    <li class="navbar"><a href='{index_html}'>Home</a></li>
    <li class="navbar"><a href='{objects_html}'>Objects</a></li>
    <li class="navbar"><a href='{samples_html}'>Samples</a></li>
</ul>
"""
HTML_FOOTER = \
"""\
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

GENERIC_VARS = ["HTML_HEADER", "HTML_TITLE", "HTML_NAVBAR", "HTML_FOOTER",
                "GENERIC_LIST_HEADER", "GENERIC_LIST_ENTRY",
                "GENERIC_LIST_FOOTER"]

# Table-related
TABLE_STYLE = \
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
<body>
<h2>PEPATAC stats summary</h2>

<table class="stats-table">                           
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

LINKS_STYLE = \
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
TABLE_VARS = ["TABLE_STYLE", "TABLE_HEADER", "TABLE_COLS",
              "TABLE_COLS_FOOTER", "TABLE_ROWS", "TABLE_FOOTER",
              "TABLE_ROWS_LINK", "LINKS_STYLE"]

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
        <p><a href='{path}'><img src='{image}'>{label}</a></p>
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

__all__ = GENERIC_VARS + TABLE_VARS + SAMPLE_VARS + OBJECTS_VARS