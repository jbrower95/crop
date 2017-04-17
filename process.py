#### Process the tokens into immediate forms.

class ROPSyntaxError(Exception):
    def __init__(self, message, corpus, location):
        # Call the base class constructor with the parameters it needs
        super(ROPSyntaxError, self).__init__("Syntax Error: {} (at line {}, character {})".format(message, whichlineandchar(corpus, location)[0], whichlineandchar(corpus, location)[1]))
        self.location = location
        self.message = message


##### Utility functions #######################################################
def whichlineandchar(text, offset):
	lines = text.split('\n')
	current_char = 0
	line = 0
	while current_char < offset:
		line_len = len(lines[line])
		if (line_len + current_char) > offset:
			# offset is in this line
			current_char = offset - current_char
			break
		current_char = current_char + line_len # add in length of previous line
		line = line + 1 # change lines
		current_char = current_char + 1 # account for newline
	return line + 1, current_char

def poptoken(tokens, pos): 
	return tokens.items()[pos], pos + 1

def peektoken(tokens, pos):
	return tokens.items()[pos]

def assertType(tokens, token, location, ttypes, corpus):
	if token["name"] not in ttypes:
		raise ROPSyntaxError("Expected token of type {}, got {}".format(ttypes, token["name"]), corpus, location)

def assertEOL(tokens, token, location, corpus):
	if token["name"] != "EOL":
		raise ROPSyntaxError("Expected token of type ';' (EOL), got {}".format(token["name"]), corpus, location)

def assertRequiresTokens(tokens, amount, pos, location, msg, corpus):
	remaining_tokens = len(tokens) - pos
	if amount > remaining_tokens: raise ROPSyntaxError(msg, corpus, location)

###############################################################################

def process(tokens, text):
	pos = 0
	DEBUG = False

	instructions = []

	if DEBUG:
		i = 0
		for key in tokens:
			print "[{} - char {}] {} (type={})".format(i, key, tokens[key]["value"], tokens[key]["name"])
			i = i + 1

	while pos < len(tokens):
		(location, token), pos = poptoken(tokens, pos)
		ttype = token["name"]

		#### Handling Comments
		if ttype == "single_line_comment":
			# skip ahead until EOL.
			cur_tok = token
			while pos < len(tokens) and cur_tok["name"] != "EOL":
				(location, cur_tok), pos = poptoken(tokens, pos)
			assertType(tokens, cur_tok, location, ["EOL"], text)
		elif ttype == "multi_line_comment_start":
			# skip ahed until closing comment.
			cur_tok = token
			while pos < len(tokens) and cur_tok["name"] != "multi_line_comment_end":
				(location, cur_tok), pos = poptoken(tokens, pos)
			assertType(tokens, cur_tok, location, ["multi_line_comment_end"], text)
		#### Handling let binding
		elif ttype == "let":
			# let | <var> = <expr> |
			assertRequiresTokens(tokens, 3, pos, location, "Expected let of the form: let <var> = <imm>", text)

			# <var>: identifier
			(loc, token), pos = poptoken(tokens, pos)
			assertType(tokens, token, loc, ["identifier"], text)
			l_value = token["value"]
			
			# assignment
			(loc, token), pos = poptoken(tokens, pos)
			assertType(tokens, token, loc, ["assign"], text)

			# parse right-hand value.
			r_value, pos = processRightValue(pos, tokens, text)
			instr = {"action" : "bind", "symbol" : l_value, "rval" : r_value}
			instructions.append(instr)

			# check for end of line, to finish statment.
			(loc, token), pos = poptoken(tokens, pos)
			assertEOL(tokens, token, loc, text)
		elif ttype == "EOL":
			# blank line
			continue
		#### Handling EOF
		elif ttype == "EOF":
			print "[+] Lexer finished."
			break
		else:
			raise ROPSyntaxError("Unexpected token {}".format(token), text, location)

	return instructions

def getRef(reftype, val):
	return {"type" : reftype, "val" : val}

def getImmRef(val):
	return getRef("imm", val)

def getSymRef(val):
	return getRef("sym", val)

def processRightValue(pos, tokens, text):
	'''
	Processes a potentially complex R value of an expression recursively.
	pos: position to start parsing from within the tokens.

	Returns: An object whose contents describe a valid r-value. (keys: symbol | action | immediate)
	'''
	final_r_value = None
	(loc, token), pos = poptoken(tokens, pos)
	r_value = token["value"]
	r_value_t = token["name"]
	assertType(tokens, token, loc, ["constant_string", "constant_numerical", "identifier"], text)

	_, next_token = peektoken(tokens, pos)
	if next_token["name"] in ["EOL", "arglist_separator", "end_apply"]:
		# Simple expression - immediately terminated after.
		final_r_value = getSymRef(r_value) if r_value_t == "identifier" else getImmRef(r_value)
	else:
		# we may have an arithmetic expression, or function application.
		lvalue = r_value # initial read becomes l_value relative to rest of expansion.
		is_identifier = token["name"] == "identifier"

		(loc, token), pos = poptoken(tokens, pos)
		assertType(tokens, token, loc, ["ma_add", "ma_subtract", "ma_multiply", "start_apply", "end_apply", "EOL", "arglist_separator"], text)
		if token["name"] == "start_apply":
			if not is_identifier:
				raise ROPSyntaxError("Error: Cannot apply() on a literal.", text, loc)
			# handle function application. (reference arguments)
			arguments = []
			_, next_token = peektoken(tokens, pos)
			while next_token["name"] != "end_apply":

				# parse an r-value (the arguments to a function are all r-values)
				arg, pos = processRightValue(pos, tokens, text)
				arguments.append(arg)

				# check to see if application is over, otherwise parse another l_value.
				(loc, next_token), pos = poptoken(tokens, pos)
				assertType(tokens, next_token, loc, ["arglist_separator", "end_apply"], text) # , or )
			final_r_value = {"action" : "apply", "sym" : lvalue, "arguments" : arguments}
		elif token["name"] in ["ma_add", "ma_subtract", "ma_multiply"]:
			# handle add, subtract, or multiply. (recursive)
			r_value, pos = processRightValue(pos, tokens, text)
			lvalue = getSymRef(lvalue) if is_identifier else getImmRef(lvalue)
			final_r_value = {"action" : token["name"], "lvalue" : lvalue, "rvalue" : r_value}
	return final_r_value, pos



