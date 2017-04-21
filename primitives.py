primitives = {
	"bin" : {
		"ma_add" : {
			"argc" : 2,							# num args required
			"func" : lambda x,y: x + y,			# anonymous function
			"expects" : ["constant_numerical", "constant_hexadecimal"],	# arg types 
			"desc" : "+"						# description
		},
		"ma_subtract" : {
			"argc" : 2,
			"func" : lambda x,y: x - y,
			"expects" : ["constant_numerical", "constant_hexadecimal"],
			"desc" : "-"
		},
		"ma_multiply" : {
			"argc" : 2,
			"func" : lambda x,y: x * y,
			"expects" : ["constant_numerical", "constant_hexadecimal"],
			"desc" : "*"
		}
	}
}