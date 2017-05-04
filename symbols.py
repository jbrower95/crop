import uuid

## Symbol vs. Immediate References 
def getRef(reftype, val, loc):
	return {"type" : reftype, "val" : val, "loc" : loc}

def rts(ref):
	desc = "(unused)" if "unused" in ref and ref["unused"] else ("(constant)" if "constant" in ref and ref["constant"] else "")
	if ref["type"] == "action":
		if ref["action"] == "apply":
			if ref["sym"]["type"] == "sym":
				return "{}({}) {}".format(rts(ref["sym"]), ",".join(map(rts, ref["args"])), desc)
			else:
				return "(*{})({}) {}".format(rts(ref["sym"]), ",".join(map(rts, ref["args"])), desc)
		if ref["action"] == "bind":
			return "{} := {} {}".format(rts(ref["sym"]), rts(ref["rvalue"]), desc)
	elif ref["type"] == "imm":
		if ref["dtype"] == "constant_hexadecimal":
			print ref
			return "{}".format(hex(ref["val"]))
		elif ref["dtype"] == "constant_string":
			return "\"{}\"".format(ref["val"])
		else:
			return "{}".format(ref["val"])
	elif ref["type"] == "sym":
		return ref["val"]

def rtsse(se):
	ropdata = "{} [{}]".format(se["roptype"], rts(se["ropdata"])) if "ropdata" in se else se["roptype"]
	return "[{: <15} {: >20}]".format(rts(se), ropdata)

def rtsse_short(se):
	ropdata = "{}({})".format(se["roptype"], rts(se["ropdata"])) if "ropdata" in se else se["roptype"]
	return "{}".format(ropdata)

def getImmRef(val, dtype, loc):
	base = getRef("imm", val, loc)
	base["dtype"] = dtype
	return base

def getSymRef(val, loc):
	return getRef("sym", val.strip(), loc)

def isImm(ref):
	return "type" in ref and ref["type"] == "imm"

def isSym(ref):
	return "type" in ref and ref["type"] == "sym"

def immIsType(ref, dtype):
	return "dtype" in ref and ref["dtype"] == dtype

def immIsTypes(ref, dtypes):
	return "dtype" in ref and ref["dtype"] in dtypes

def immsAreTypes(refs, dtypes):
	return reduce(lambda x,y: x and y, map(lambda ref: immIsTypes(ref, dtypes), refs))

def refRequiresTemp(ref):
	# ref will need to be moved to a temporary variable if function application used.
	return ref["type"] == "action" and ref["action"] == "apply"

def str2words(s, WORD_SIZE):
	s = s + "." # to save room for null byte
	# Assume each character is a byte, and each cell is a word.
	assert WORD_SIZE > 0 and WORD_SIZE % 4 == 0, "Word size must be a multiple of 4 and non-zero."
	return [s[0+i:WORD_SIZE+i] for i in range(0, len(s), WORD_SIZE)]

def printStackPayload(payload, ESP=-1):
	'''
	Prints a stack payload, with %esp
	as an index into the payload.

	%esp set to 0 will start from the bottom of the payload,
	with the max value of esp at len(payload)
	'''
	stack_entries = payload["stack"]
	data_divider = payload["data_begins"]
	print "---------payload----------"
	i = 0
	for se in reversed(stack_entries):
		print rtsse(se),
		if ESP == (len(stack_entries) - i - 1):
			print "<---- (%esp)  ",
		if data_divider == (len(stack_entries) - i - 1):
			print "<---- (data region)  ",
		print ""
		i = i + 1
	print "--------------------------"

## Function applications
def makeAction(action, loc):
	return {"type" : "action", "action" : action, "loc" : loc}

def makeBindAction(sym, rvalue, loc):
	base = makeAction("bind", loc)
	base["sym"] = getSymRef(sym.strip(), loc)
	base["rvalue"] = rvalue
	return base

def makeBindActionRaw(sym, rvalue, loc):
	base = makeAction("bind", loc)
	base["sym"] = sym
	base["rvalue"] = rvalue
	return base

def makeApplyActionRaw(sym, args, loc, argc=-1):
	base = makeAction("apply", loc)
	if argc == -1: argc = len(args)
	base["sym"] = sym
	base["argc"] = argc
	base["args"] = args
	return base

def makeTemporaryBindAction(rvalue, loc):
	base = makeAction("bind", loc)
	varname = "tvar-{}".format(str(uuid.uuid4())[0:10])
	base["sym"] = getSymRef(varname, None)
	base["rvalue"] = rvalue
	return base

def makeApplyAction(sym, args, loc, argc=-1):
	base = makeAction("apply", loc)
	if argc == -1: argc = len(args)
	base["sym"] = getSymRef(sym.strip(), loc)
	base["argc"] = argc
	base["args"] = args
	return base


def removeVerboseEntries(action):
	'''
	Removes annoying entries like 'loc'.
	'''
	action = deepcopy(action)
	if "loc" in action:
		del action["loc"]
	for key in action:
		if type(action[key]) is dict:
			action[key] = removeVerboseEntries(action[key])
		if type(action[key]) is list:
			action[key] = [removeVerboseEntries(x) for x in action[key]]
	return action
