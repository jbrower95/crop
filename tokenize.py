from collections import OrderedDict
from process import ROPSyntaxError
import re

def linesToTokens():
	pass

def has(data, offset, pattern):
	'''
	Returns true if, at the given offset, you can read 'pattern'
	from data.
	'''
	if offset + len(pattern) > len(data): return False
	return data[offset:offset+len(pattern)] == pattern

def grabWhileIn(data, offset, pattern):
	'''
	Returns a variable length substring of data, starting from offset,
	containing only the characters in pattern.
	'''
	return grabUntil(data, offset, lambda data,i: data[i] not in pattern)

def grabUntil(data, offset, fun):
	'''
	Returns a variable length substring of data, starting from offset,
	containing only the characters in pattern.
	'''
	max_len = len(data)-offset
	end = len(data)
	for i in range(offset, offset + max_len):
		if fun(data, i): 
			end = i
			break
	return data[offset:end]

def mktok(tok, char, location=None, value=None,force=False):
	base = {"name" : tok, "chr" : char, }
	if location: base["location"] = {"line" : location[0], "char" : location[1]}
	if value or force: base["value"] = value
	return base

IDENTIFIER_TOKENS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
NUMBER_TOKENS = "0123456789"
HEX_TOKENS = NUMBER_TOKENS + "abcdefABCDEF"

def tokenize(corpus):
	# Load tokens, in order.
	collected_tokens = []

	i = 0
	line = 0
	char = 0
	while i < len(corpus):
		if corpus[i] == '\n':
			char, line = 0, line + 1
			i = i + 1
		elif corpus[i] == ";":
			collected_tokens.append(mktok("EOL", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == "$":
			collected_tokens.append(mktok("deref", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == '(':
			collected_tokens.append(mktok("start_apply", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == ')':
			collected_tokens.append(mktok("end_apply", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == ',':
			collected_tokens.append(mktok("arglist_separator", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == "=" and not has(corpus, i, "=="):
			collected_tokens.append(mktok("assign", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == "+":
			collected_tokens.append(mktok("ma_add", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == "-":
			collected_tokens.append(mktok("ma_subtract", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif corpus[i] == "*":
			collected_tokens.append(mktok("ma_multiply", i, location=(line,char)))
			i = i + 1
			char = char + 1
		elif has(corpus, i, "=="):
			collected_tokens.append(mktok("equals", i, location=(line,char)))
			i = i + 2
			char = char + 2
		elif has(corpus, i, "//"):
			i = i + 2 # advance past the comment marker.
			char = char + 2
			val = grabUntil(corpus, i, lambda data,i: data[i] == "\n")
			collected_tokens.append(mktok("single_line_comment", i, location=(line,char), value=val))
			i = i + len(val)
			char = char + len(val)
		elif has(corpus, i, "/*"):
			i = i + 2
			char = char + 2
			val = grabUntil(corpus, i, lambda data,i: data[i] == "/" and data[i-1] == "*")[:-1]
			collected_tokens.append(mktok("multi_line_comment", i, location=(line,char), value=val))
			i = i + len(val) + 2
			char = char + len(val) + 2
		elif has(corpus, i, "let"):
			collected_tokens.append(mktok("let",i,location=(line,char)))
			i = i + 3
			char = char + 3
		elif has(corpus, i, "if"):
			collected_tokens.append(mktok("if",i,location=(line,char)))
			i = i + 2
			char = char + 2
		elif has(corpus, i, "while"):
			collected_tokens.append(mktok("while",i,location=(line,char)))
			i = i + 5
			char = char + 5
		elif not corpus[i].isspace():
			# Read constants + identifiers.
			val = None
			val_class = None
			val_len = 0
			if corpus[i] in IDENTIFIER_TOKENS:
				val = grabWhileIn(corpus, i, IDENTIFIER_TOKENS)
				val_class = "identifier"
				val_len = len(val)
			elif has(corpus, i, "0x"):
				i = i + 2
				val = grabWhileIn(corpus, i, HEX_TOKENS)
				val_class = "constant_hexadecimal"
				val_len = len(val)
				val = int(val, 16)
			elif corpus[i] in NUMBER_TOKENS:
				val = grabWhileIn(corpus, i, NUMBER_TOKENS)
				val_len = len(val)
				val = int(val)
				val_class = "constant_numerical"
			elif corpus[i] == "\"":
				i = i + 1
				char = char + 1
				val = grabUntil(corpus, i, lambda data, i: data[i] == '"' and data[i-1] != "\\")
				val_len = len(val)
				val_class = "constant_string"
				i = i + 1
				char = char + 1
			else:
				raise ROPSyntaxError("Unexpected token {}".format(corpus[i]), {"line":line,"char":char})
			i = i + val_len
			collected_tokens.append(mktok(val_class,i,location=(line,char),value=val,force=True))
			char = char + val_len
		else:
			i = i + 1
			char = char + 1
	collected_tokens.append(mktok("EOF", i, location=(line,char)))
	return collected_tokens