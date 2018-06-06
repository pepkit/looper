""" Html constants """

__author__ = "Jason Smith"
__email__ = "jasonsmith@virginia.edu"

# Table-related
TABLE_STYLE = (
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
)
TABLE_HEADER = (
"""
<body>
<h2>PEPATAC stats summary</h2>

<table class="stats-table">                           
    <thead>
        <tr class="stats-firstrow">
"""
)
TABLE_COLS = (
"""\
            <th>{col_val}</th>
"""
)
TABLE_COLS_FOOTER = (
"""\
        </tr>
    </thead>
    <tbody>
        <tr>
"""
)

TABLE_ROWS = (
"""\
            <td>{row_val}</td>
"""
)
TABLE_FOOTER = (
"""\
        </tr>
    </tbody>
</table>
"""
)
TABLE_ROWS_LINK = (
"""\
            <td style="cursor:pointer" onclick="location.href='{html_page}'"><tlinks class="LN1 LN2 LN3 LN4 LN5" href="{page_name}" target="_top">{link_name}</a></td>
"""
)
LINKS_STYLE = (
"""
tlinks.LN1 {
  font-style:normal;
  font-weight:bold;
  font-size:1.0em;
}

tlinks.LN2:link {
  color:#A4DCF5;
  text-decoration:none;
}

tlinks.LN3:visited {
  color:#A4DCF5;
  text-decoration:none;
}

tlinks.LN4:hover {
  color:#A4DCF5;
  text-decoration:none;
}

tlinks.LN5:active {
  color:#A4DCF5;
  text-decoration:none;
}
"""
)

TABLE_VARS = ["TABLE_STYLE", "TABLE_HEADER", "TABLE_COLS",
              "TABLE_COLS_FOOTER", "TABLE_ROWS", "TABLE_FOOTER",
              "TABLE_ROWS_LINK", "LINKS_STYLE"]

# Sample-page-related
SAMPLE_HEADER = (
"""\
<html>
<h1>{sample_name} figures</h1>
    <body>
        <p><a href='{index_html}'>Return to summary page</a></p>

"""
)
SAMPLE_PLOTS = (
"""\
        <p><a href='{path}'><img src='{image}'>{label}</a></p>
"""
)
SAMPLE_FOOTER = (
"""
        <p><a href='{index_html}'>Return to summary page</a></p>
    </body>
</html>
"""
)

SAMPLE_VARS = ["SAMPLE_HEADER", "SAMPLE_PLOTS", "SAMPLE_FOOTER"]

__all__ = TABLE_VARS + SAMPLE_VARS