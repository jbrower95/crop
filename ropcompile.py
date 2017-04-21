from symbols import *
from copy import deepcopy

def unusedOrConstant(expr):
	return ("unused" in expr and expr["unused"]) or ("constant" in expr and expr["constant"]) 

def sym2retaddr(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "RET_ADDR"
	return sym

def sym2emptyref(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "<empty>"
	return sym

def sym2arg(sym, argi):
	sym = deepcopy(sym)
	sym["roptype"] = "ARG"
	sym["ropdata"] = argi
	return sym

def imm2esplift(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "ESP_LFT"
	sym["ropdata"] = sym["val"]
	return sym

def emptyAddrRef():
	return sym2retaddr(getImmRef(0, "constant_hexadecimal", None))

def emptyRef():
	return sym2emptyref(getImmRef(0, "constant_hexadecimal", None))

def esplift(amt):
	return imm2esplift(getImmRef(amt, "constant_numerical", None))

def reserve(stack, upTo):
	while len(stack) < upTo:
		stack.append(emptyRef())

def ropcompile(actions, symtable, sequences, DEBUG=False):
	'''
	Given a bunch of ROP gadgets, compile a payload (or attempt to.)

	actions - The actions the program has requested.
	symtable - The symtable for this set of actions.

	'''
	# TODO: Resolve primitives of gadgets.
	# TODO: Convert local vars into register assignment.
	# TODO: register spilling 
	# TODO: determine basic block side-effects.
	# TODO: Given primitives + register assignments, compile payload.

	stack = [] # eventually, a high level form of the compiled payload. 0 is the lowest address in memory.
	sp = 0	# an index into stack.
	intermediateExprs = [] # a set of assignment actions to perform, prior to a call.
	
	regTable = {} # a stateful map of <var -> register>
	varTable = {} # a stateful map of <var -> stack slot>

	# index of the next gadget
	next_gadget = 0
	stack.append(emptyAddrRef()) # for the first gadget
	stack.append(emptyAddrRef()) # for the second gadget

	for idx, action in enumerate(actions):
		if unusedOrConstant(action):
			# Skip variable allocation for variables that are unused / constant.
			print "[compile] skipping {}".format(rts(action))
			continue
		if action["type"] == "action":
			if action["action"] == "bind":
				# Wait until an application to bind
				intermediateExprs.append(action)
			elif action["action"] == "apply":
				# See if anything needs to be bound
				print "[compile] processing {}".format(rts(action))
				stack[next_gadget] = sym2retaddr(action["sym"]) # addr to call.
				reserve(stack, next_gadget + 1 + len(action["args"]))
				if action["args"]:
					for idx, arg in enumerate(action["args"]):
						stack.append(sym2arg(arg, idx)) # args in reversed order
					next_gadget = next_gadget + 1
					# request ESP lift.
					stack[next_gadget] = esplift(len(action["args"]))
					next_gadget = next_gadget + len(action["args"])
				else:
					# no ESP lift required.
					next_gadget = next_gadget + 1
	return stack