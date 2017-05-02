from symbols import *
from copy import deepcopy
from operator import itemgetter
from primitives import primitives

class ROPCompilationError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ROPCompilationError, self).__init__("Compilation Error: {}".format(message))


def unusedOrConstant(expr):
	return ("unused" in expr and expr["unused"]) or ("constant" in expr and expr["constant"]) 

def sym2retaddr(sym):
	sym = deepcopy(sym)
	print sym
	if sym["dtype"] == "constant_numerical": 
		sym["dtype"] = "constant_hexadecimal"
	sym["roptype"] = "CALL"
	return sym

def sym2emptyref(sym, val="<empty>"):
	sym = deepcopy(sym)
	sym["roptype"] = val
	return sym

def sym2arg(sym, argi):
	sym = deepcopy(sym)
	sym["roptype"] = "ARG"
	sym["ropdata"] = argi
	return sym

def imm2esplift(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "ESP_LFT"
	sym["ropdata"] = sym
	return sym

def emptyAddrRef():
	return sym2retaddr(getImmRef(0, "constant_hexadecimal", None))

def emptyPaddingRef():
	return sym2emptyref(getImmRef(0, "constant_hexadecimal", None), val="<padding>")

def dataReadRef(fromPlace):
	sym["type"] = "builtin"
	sym["roptype"] = "G_READ"
	sym["ropdata"] = fromPlace
	return sym

def dataWriteRef(fromPlace, intoPlace):
	sym = deepcopy(intoPlace)
	sym["roptype"] = "G_WRITE"
	sym["ropdata"] = fromPlace
	return sym

def emptyRef():
	return sym2emptyref(getImmRef(0, "constant_hexadecimal", None))

def imm2dataRef(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "DATA"
	sym["ropdata"] = sym
	return sym

def imm2constRef(sym):
	sym = deepcopy(sym)
	sym["roptype"] = "CONST"
	return sym


def dataRef(idx):
	return imm2dataRef(getImmRef(idx, "constant_numerical", None))

def esplift(amt):
	return imm2esplift(getImmRef(amt, "constant_numerical", None))

def stack_entry_gadget(gtype, vaddr):
	sym = getImmRef(vaddr, "constant_hexadecimal", None)
	sym["roptype"] = "GADGET"
	sym["ropdata"] = getImmRef(gtype, "string", None)
	return sym

def resolvedEspLift(gadget):
	return {
		"roptype" : ""
	}

def reserve(stack, upTo):
	print "[stack] Reserving stack space up to index {}.".format(upTo)
	while len(stack) <= upTo:
		stack.append(emptyRef())

def printStackInfo(stack):
	print "[stack] size = {}".format(len(stack))

def isBuiltIn(sym):
	for ftype in primitives:
		if sym["val"] in primitives[ftype]:
			return ftype
	return ""

def precompile_payload(actions, symtable, sequences, DEBUG=False):
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
	data = [] # data units to be held at the top of the stack.

	sp = 0	# an index into stack.
	intermediateExprs = [] # a set of assignment actions to perform, prior to a call.
	
	regTable = {} # a stateful map of <var -> register>
	varTable = {} # a stateful map of <var -> stack slot>
	dataTable = {} # a stateful map of <const_str -> idx>

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
				print "[compile] saving {}".format(rts(action))
				if isImm(action["rvalue"]) and action["rvalue"]["dtype"] == "constant_string":
					print action
					varsym = action["sym"]
					print "[compile] Storing str value {} in data portion of stack.".format(varsym)
					data.append(action["rvalue"]["val"])
					dataTable[varsym["val"]] = len(data) - 1 
				intermediateExprs.append(action)
			elif action["action"] == "apply":
				# See if anything needs to be bound
				print "[compile] processing {}".format(rts(action))
				reserve(stack, next_gadget + 1 + len(action["args"]))
				ftype = isBuiltIn(action["sym"])
				if not ftype:
					stack[next_gadget] = sym2retaddr(action["sym"]) # addr to call.
					if action["args"]:
						argbase = next_gadget + 2
						for idx, arg in enumerate(action["args"]):
							if arg["type"] == "sym" and arg["val"] in dataTable:
								print "[compile] Resolving str variable {}".format(rts(arg))
								print "[compile] * stored at payload idx {}".format(argbase + idx)
								stack[argbase + idx] = dataRef(dataTable[arg["val"]])
							else:
								stack[argbase + idx] = sym2arg(arg, getImmRef(idx, "constant_numerical", None)) # args in reversed order
						next_gadget = next_gadget + 1
						# request ESP lift.
						stack[next_gadget] = esplift(len(action["args"]))
						next_gadget = next_gadget + len(action["args"]) + 1
					else:
						# no ESP lift required. Just tick forward to the next gadget.
						next_gadget = next_gadget + 1
				else:
					# built in! see what we got.
					if ftype == "std":
						reserve(stack, next_gadget + 1) # no arguments.
						# the 'crop' standard functions.
						f_args = action["args"]
						if action["sym"]["val"] == "mem_write":
							stack[next_gadget] = dataWriteRef(f_args[0], f_args[1])
						next_gadget = next_gadget + 1 
					print 'uh'
		printStackInfo(stack)
		print "Next gadget: {}".format(next_gadget)
	# Concatenate data region onto the stack.
	begin_data = len(stack)
	for val in data:
		stack.extend(map(lambda v: imm2constRef(getImmRef(v, "constant_string", None)), str2words(val, 4)))
	return {"data_begins" : begin_data, "stack" : stack, "data" : data, "data_table" : dataTable}

def find_esp_lift(gadgets, at_least):
	# Look for all ESP lifts of atleast 'at_least'.
	candidates = filter(lambda g: g["AMT"] > at_least, gadgets)
	# sort the list so that the most appropriate candidate is first.
	# that is, the ESP lift which is closest to being 'at_least'.
	candidates = sorted(candidates, key=itemgetter('AMT'))
	return candidates

def insert_padding(payload, at, amt):
	# Inserts <amt> number of padding references into the payload at index <at>.
	for _ in range(amt): payload.insert(at, emptyPaddingRef())

def resolveESPlifts(payload, gadgets, DEBUG=True):
	stack_payload = payload["stack"]
	i = 0
	while i < len(stack_payload):
		item = stack_payload[i]	
		if item["roptype"] == "ESP_LFT":
			at_least = item["ropdata"]["val"]
			candidates = find_esp_lift(gadgets, at_least)
			if not candidates:
				raise ROPCompilationError("No candidate sequence for {}".format(rtsse_short(item)))
			else:
				# pick the first candidate.
				lift = candidates[0]
				overshoot = lift["AMT"] - at_least
				if overshoot:
					print "ESP Lift too large ({} > {}). Requires {} padding.".format(lift["AMT"], at_least, overshoot)
					# arguments will finish after "at_least", so we'll want to insert there.
					insert_padding(stack_payload, i+at_least+1, overshoot)
				# Patch in the correct address.
				stack_payload[i] = stack_entry_gadget("ESP_LIFT", lift["vaddr"])
				payload["data_begins"] += overshoot
		i = i + 1

def resolveVar():
	pass


def compile_payload(payload, gadgets, DEBUG=True):
	'''
	Given the previous stage compilation, and the available gadgets, compile
	a payload.
	'''
	
	# start ESP at 0.
	esp = 0

	# resolve all ESP lifts.
	resolveESPlifts(payload, gadgets["esp_lift"], DEBUG=DEBUG)





	return payload
















