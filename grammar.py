

grammar = {
	"tokens" : [
		{
			"name" : "let",
			"regex" : r"(\A|\b)let"
		},
		{
			"name" : "single_line_comment",
			"regex" : r"//(.*)$"
		},
		{
			"name" : "multi_line_comment_start",
			"regex" : r"/[*]+"
		},
		{
			"name" : "multi_line_comment_end",
			"regex" : r"[*]+/"
		},
		{
			"name" : "EOL",
			"regex" : r";"
		},
		{
			"name" : "ma_add",
			"regex" : r"\+"
		},
		{
			"name" : "ma_subtract",
			"regex" : r"\-"
		}, 
		{
			"name" : "ma_multiply",
			"regex" : r"\*"
		},
		{
			"name" : "if",
			"regex" : r"\bif\b"
		},
		{
			"name" : "assign",
			"regex" : r"\s+=\s+"
		},
		{
			"name" : "equals",
			"regex" : r"\s==\s"
		},
		{
			"name" : "start_apply",
			"regex" : r"\("
		},
		{
			"name" : "end_apply",
			"regex" : r"\)"
		},
		{
			"name" : "arglist_separator",
			"regex" : r","
		},
		{
			"name" : "constant_string",
			"regex" : r"\".*\""
 		},
		{
			"name" : "constant_numerical",
			"regex" : r"[0-9]+",
			"transform" : (lambda val: int(val))
		},
		{
			"name" : "identifier",
			"regex" : r"(\s+|\w|^)(?!let)(?!if)[a-z]+(\s*)"
		}
	]
}


