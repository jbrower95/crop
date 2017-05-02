from process import ROPSyntaxError
from primitives import primitives
from copy import deepcopy
from symbols import *

def flatten(actions, optimize=True, DEBUG=False):
	'''
	Given a bunch of actions, flatten them as best as possible.

	i.e:
	
	let y = 4;
	let x = 10 + y;

	'''
	output_actions = []
	for action in actions:
		if DEBUG: print "Flattening " + rts(action)
		if action["action"] == "bind":
			# a variable binding (let <sym> = <rval>)
			r_value = action["rvalue"]
			setup, r_value = flatten_rvalue(r_value, DEBUG=DEBUG)
			action["rvalue"] = r_value
			output_actions.extend(setup)
		else:
			# any expression (<rval>)
			setup, action = flatten_rvalue(action, DEBUG=DEBUG)
			output_actions.extend(setup)
		output_actions.append(action)
	return output_actions, output_actions != actions

def flatten_rvalue(rvalue, DEBUG=False):
	setup = []
	rvalue = deepcopy(rvalue)
	if rvalue["type"] == "action":
		if rvalue["action"] == "apply":
			if isSym(rvalue["sym"]) and rvalue["sym"]["val"] in primitives["bin"]:
				# _!!__ Binary Operator Optimizations __!!___
				if DEBUG: print "Attempting to optimize binary operator."
				prim = primitives["bin"][rvalue["sym"]["val"]]
				if isImm(rvalue["args"][0]) and isImm(rvalue["args"][1]):
					expected_types = prim["expects"]
					expected_type = expected_types[0]
					if not immsAreTypes(rvalue["args"], expected_types):
						raise ROPSyntaxError("{}: Expected arguments of type(s) '{}'".format(rvalue["sym"], expected_type))
					else:
						# These are totally collapsable.
						rvalue = getImmRef(prim["func"](*map(lambda x: x["val"], rvalue["args"])), expected_type, None)
						if DEBUG: print "Collapsed rvalue to {}".format(rts(rvalue))
				elif isImm(rvalue["args"][0]) or isImm(rvalue["args"][1]):
					# one of them is primitive. check for special cases.
					optimizedArg = rvalue["args"][(0 if isImm(rvalue["args"][0]) else 1)]
					other = 1 if optimizedArg == rvalue["args"][0] else 0
					if rvalue["sym"] == "ma_add" and optimizedArg["val"] == 0:
						# adding nothing -- default to other r-value.
						rvalue = other
					elif rvalue["sym"] == "ma_multiply":
						if optimizedArg["val"] == 0:
							# mult w/ zero = 0
							rvalue = getImmRef(0, "constant_numerical", None)
						elif optimizedArg["val"] == 1:
							rvalue = other
	if rvalue["type"] == "action" and rvalue["action"] == "apply":
		# General function flattening.
		print "Flattening r-val: {}".format(rvalue)
		for i in range(len(rvalue["args"])):
			arg = rvalue["args"][i]
			# Try to reduce the argument
			print "Attempting to flatten arg #{}: {}".format(i, arg)
			arg_setup, arg = flatten_rvalue(arg)
			setup.extend(arg_setup)
			rvalue["args"][i] = arg
			if refRequiresTemp(arg):
				# If it actually reduces and requires setup
				if DEBUG: print "Moving out arg #{} of {} to temporary variable.".format(i, rts(rvalue["sym"]))
				# Move this out to a temporary binding.
				extra_step = makeTemporaryBindAction(arg, arg["loc"])
				setup.append(extra_step)
				if DEBUG: print "Extra setup: {}".format(rts(extra_step))
				rvalue["args"][i] = extra_step["sym"]
				if DEBUG: print "Reassigned arg to: " + rts(rvalue["args"][i]) 
	return setup, rvalue
