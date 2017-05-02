from symbols import getRef, getImmRef, getSymRef, makeBindAction, makeApplyAction
from primitives import primitives

#### Process the tokens into immediate forms.
class ROPSyntaxError(Exception):
    def __init__(self, message, location):
        # Call the base class constructor with the parameters it needs
        super(ROPSyntaxError, self).__init__("Syntax Error: {} (at line {}, character {})".format(message, location["line"], location["char"]))
        self.location = location
        self.message = message

def poptoken(tokens, pos): 
	return tokens[pos], pos + 1

def peektoken(tokens, pos):
	return tokens[pos]

def assertType(tokens, token, ttypes):
	if token["name"] not in ttypes:
		raise ROPSyntaxError("Expected token of type {}, got {}".format(ttypes, token["name"]), token["location"])

def assertEOL(tokens, token):
	if token["name"] != "EOL":
		raise ROPSyntaxError("Expected token of type ';' (EOL), got {}".format(token["name"]), token["location"])

def assertRequiresTokens(tokens, amount, pos, msg):
	remaining_tokens = len(tokens) - pos
	if amount > remaining_tokens: raise ROPSyntaxError(msg, corpus, location)

###############################################################################

def process(tokens, text):
	pos = 0
	DEBUG = False

	instructions = []

	while pos < len(tokens):
		token, pos = poptoken(tokens, pos)
		ttype = token["name"]
		print "Current token: " + ttype;

		#### Handling Comments
		if ttype == "single_line_comment" or ttype == "multi_line_comment":
			# no reason to do anything.
			if DEBUG: print "Processed comment: {}".format(token["value"])
		#### Handling let binding
		elif ttype == "let":
			# let | <var> = <expr> |
			assertRequiresTokens(tokens, 3, pos, "Expected let of the form: let <var> = <imm>")

			# <var>: identifier
			token, pos = poptoken(tokens, pos)
			tloc = token["location"]
			assertType(tokens, token, ["identifier"])
			l_value = token["value"]
			
			# assignment
			token, pos = poptoken(tokens, pos)
			assertType(tokens, token, ["assign"])

			# parse right-hand value.
			r_value, pos = processRightValue(pos, tokens)

			# Form the action for the compiler
			instructions.append(makeBindAction(l_value, r_value, tloc))

			# check for end of line, to finish statment.
			token, pos = poptoken(tokens, pos)
			assertEOL(tokens, token)
		elif ttype == "EOL":
			# blank line
			continue
		elif ttype == "EOF":
			break
		else:
			# Could be a function call / rvalue in general. read it.
			# -1 to include the current token in this parse.
			val, pos = processRightValue(pos - 1, tokens)
			instructions.append(val)

	return instructions


def processArgumentList(pos, tokens):
	'''
	Process a list of expressions, followed by ",".
	'''
	exprs = []

	if peektoken(tokens, pos)["type"] != "end_apply":
		# no exprs in expr list.
		return pos + 1, exprs

	# Read at least one expression. <expr>
	expr, pos = processExpression(pos, tokens)
	exprs.append(expr)

	# Potentially a variable number of exprs. <expr>, <expr>
	while peektoken(tokens, pos)["type"] != "end_apply":
		if peektoken(tokens, pos)["type"] == "arglist_separator":
			# Skip over the ','.
			_, pos = poptoken(tokens, pos)
		else:
			# Read an expression.
			expr, pos = processExpression(pos, tokens)
			exprs.append(expr)
	return exprs

def processExpression(pos, tokens):
	'''
	Processes a potentially complex R value of an expression recursively.
	pos: position to start parsing from within the tokens.

	Returns: An object whose contents describe a valid r-value. (keys: symbol | action | immediate)
	'''
	final_r_value = None
	token, pos = poptoken(tokens, pos)
	print "Processing: {}".format(token)
	r_value = token["value"] if "value" in token else ""
	r_value_t = token["name"];
	assertType(tokens, token, ["constant_string", "constant_numerical", "constant_hexadecimal", "identifier"])


def processRightValue(pos, tokens):
	'''
	Processes a potentially complex R value of an expression recursively.
	pos: position to start parsing from within the tokens.

	Returns: An object whose contents describe a valid r-value. (keys: symbol | action | immediate)
	'''
	final_r_value = None
	token, pos = poptoken(tokens, pos)
	print "Processing: {}".format(token)
	r_value = token["value"]
	r_value_t = token["name"]
	assertType(tokens, token, ["constant_string", "constant_numerical", "constant_hexadecimal", "identifier"])

	next_token = peektoken(tokens, pos)
	if next_token["name"] in ["EOL", "arglist_separator", "end_apply"]:
		# Simple expression - immediately terminated after.
		final_r_value = getSymRef(r_value, next_token["location"]) if r_value_t == "identifier" else getImmRef(r_value, r_value_t, next_token["location"])
	else:
		# we may have an arithmetic expression, or function application.
		lvalue = r_value # initial read becomes l_value relative to rest of expansion.
		is_identifier = token["name"] == "identifier"

		token, pos = poptoken(tokens, pos)
		assertType(tokens, token, ["ma_add", "ma_subtract", "ma_multiply", "start_apply", "end_apply", "EOL", "arglist_separator"])
		if token["name"] == "start_apply":
			floc = next_token["location"]
			if not is_identifier:
				raise ROPSyntaxError("Error: Cannot apply() on a literal.", token["location"])
			# handle function application. (reference arguments)
			arguments = []
			next_token = peektoken(tokens, pos)
			while next_token["name"] != "end_apply":
				# parse an r-value (the arguments to a function are all r-values)
				arg, pos = processRightValue(pos, tokens)
				arguments.append(arg)

				# check to see if application is over, otherwise parse another l_value.
				next_token, pos = poptoken(tokens, pos)
				assertType(tokens, next_token, ["arglist_separator", "end_apply"]) # , or )
			if peektoken(tokens, pos)["name"] == "end_apply":
				# pop it off.
				token, pos = poptoken(tokens, pos)
			final_r_value = makeApplyAction(lvalue.strip(),arguments, floc, argc=len(arguments))
		elif token["name"] in primitives["bin"]:
			# handles binary-infix primitives.
			rvalue, pos = processRightValue(pos, tokens)
			lvalue = getSymRef(lvalue, token["location"]) if is_identifier else getImmRef(lvalue, r_value_t, token["location"])
			final_r_value = makeApplyAction(token["name"].strip(), [lvalue, rvalue], token["location"], argc=2)
	return final_r_value, pos



