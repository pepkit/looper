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

TABLE_CONSTANTS = ["TABLE_STYLE", "TABLE_HEADER", "TABLE_COLS",
                   "TABLE_COLS_FOOTER", "TABLE_ROWS", "TABLE_FOOTER"]

__all__ = TABLE_CONSTANTS