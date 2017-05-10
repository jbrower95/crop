from symbols import *
from primitives import primitives
import grako

#### Process the tokens into immediate forms.
class ROPSyntaxError(Exception):
    def __init__(self, message, location):
        # Call the base class constructor with the parameters it needs
        super(ROPSyntaxError, self).__init__("Syntax Error: {} (at line {}, character {})".format(message, location["line"], location["char"]))
        self.location = location
        self.message = message

def processAST(ast):
	'''
	returns a list of <actions> to give to the rest of the compiler.
	'''
	stmts = []
	for statement in ast:
		assert len(statement) == 2 and statement[1] == ";"
		contents = statement[0]
		contents_normalized = normalizeExpression(contents)
		stmts.append(contents_normalized)
	return stmts

# AST dict 2 location. convenience method returns (line, char) pairs.
def ast2l(pi): 
	try:
		return {"line" : pi["parseinfo"].line, "char" : pi["parseinfo"].pos}
	except TypeError as e:
		print "Error parsing '{}' - {}".format(pi, e)
		raise Exception("Uncaught.")

def normalizeExpression(ast):
	'''
	Attempts to recursively normalize a Grako AST to fit our compiler spec.
	Just renames some things.
	'''
	action = None
	#print "Processing {}".format(ast)
	root_loc = ast2l(ast)
	ttype = ast["parseinfo"].rule

	if ttype == "bind":
		# Parse variable binding. (let <id> = <expr>)
		identifier = ast["id"]
		identifier_location = ast2l(identifier)

		lvalue = normalizeExpression(identifier) 
		rvalue = normalizeExpression(ast["rval"])

		action = makeBindActionRaw(lvalue, rvalue, root_loc)
	elif ttype == "function_application":
		# 1. normalize all arguments. (filter for AST arguments only -- everything else is garbage.)
		#
		#  For example, on empty invocations (e.g call()), grako will leave behind
		#  call : { args: ["(", ")"]}, which aren't even AST members. /shrug?
		args = map(normalizeExpression, filter(lambda x: type(x) is grako.ast.AST, ast["args"]))
		
		# 2. normalize identifier / constant.
		fid = normalizeExpression(ast["id"])

		# 3. formulate action.
		action = makeApplyActionRaw(fid, args, fid["loc"])
	elif ttype == "inline_application":
		print ast

		expr = ast["bin_function"]
		fargs = [expr[0], expr[2]] # <arg1> + <arg2>  --> 0, 2 are args
		fargs = map(normalizeExpression, fargs)

		fname = expr[1]
		for operator in primitives["bin"]:
			if fname == primitives["bin"][operator]["desc"]:
				real_fname = operator
				break
		assert real_fname, "Unknown operator"

		# TODO: This is technically wrong -- we should propogate metadata about binary operators.
		inline_sym_ref = getSymRef(real_fname, root_loc)
		action = makeApplyActionRaw(inline_sym_ref, fargs, root_loc)
	elif ttype == "identifier":
		# Parse identifiers.
		action = getSymRef(ast["val"], ast2l(ast))
	elif ttype in ["constant_numerical", "constant_hexadecimal", "constant_string"]:
		# Parse constant types.
		val = ast["val"]

		# add ur own bases here lol
		mappers = {
			"constant_numerical" : lambda x: int(x, 10),
			"constant_hexadecimal" : lambda x: int(x, 16),
			"constant_string" : lambda x: x[1:][:-1]
		}
		
		action = getImmRef(mappers[ttype](val), ttype, ast2l(ast))
	else:
		print ast["parseinfo"].rule
	return action

