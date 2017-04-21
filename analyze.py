from symbols import *
from copy import deepcopy

def action_references_symbol(action, sym, DEBUG=False):
	if action["type"] == "action" and action["action"] == "bind":
		# If it's a bind, return true if the rval is used. 
		#
		# This is technically more complicated, since a reassignment might detach the variable.
		# But whatever
		return action["sym"]["val"] == sym["val"] or action_references_symbol(action["rvalue"], sym)
	elif action["type"] == "sym":
		# If it's a symbol, return true if correct symbol.
		return action["val"] == sym["val"]
	elif action["type"] == "action" and action["action"] == "apply":
		# If it's an apply, check the function symbol + all args.
		return action["sym"]["val"] == sym["val"] or (action["args"] and reduce(lambda x,y: x or y, map(lambda a: action_references_symbol(a, sym), action["args"])))
	else:
		# Could be an immediate constant, or something else.
		return False

def action_replace_symbol(action, sym, alternateSym, DEBUG=False):
	original_action = deepcopy(action)
	if action["type"] == "action" and action["action"] == "bind":
		# If it's a bind, return true if the rval is used. 
		#
		# This is technically more complicated, since a reassignment might detach the variable.
		# But whatever
		return action_replace_symbol(action["rvalue"], sym, alternateSym)
	elif action["type"] == "sym":
		# If it's a symbol, return true if correct symbol.
		if action["val"] == sym["val"]:
			for key in alternateSym:
				action[key] = alternateSym[key]
			return True
		return False
	elif action["type"] == "action" and action["action"] == "apply":
		# If it's an apply, check the function symbol + all args.
		result = False
		if action["sym"]["val"] == sym["val"]:
			action["sym"] = alternateSym
			result = True

		for i in range(len(action["args"])):
			arg = action["args"][i]
			result = action_replace_symbol(arg, sym, alternateSym) or result
		if result:
			if DEBUG: print "[analyzer] Did substitution: {} => {}".format(rts(original_action), rts(action))
		return result
	else:
		return False

def propogateConstants(actions, DEBUG=False):
	for i in range(len(actions)):
		action = actions[i]
		if action["type"] == "action" and action["action"] == "bind":
			symbol = action["sym"]
			# check to see if it is a constant, replacable.
			if isImm(action["rvalue"]):
				action["constant"] = True
				hits = 0
				for j in range(i+1, len(actions)):
					# direct substitution
					if action_replace_symbol(actions[j], symbol, action["rvalue"], DEBUG=DEBUG):
						hits = hits + 1
					if actions[j]["type"] == "action" and actions[j]["action"] == "bind" and actions[j]["sym"] == symbol:
						if DEBUG: print "[analyzer] [!] Stopped constant substitution bc of rebinding (at {}).".format(actions[j])
						break
	return actions

def generateSymTable(actions, DEBUG=False):
	sym_table = {}
	for i in range(len(actions)):
		action = actions[i]
		if action["type"] == "action" and action["action"] == "bind":
			# variable binding. introduce this.
			symbol = action["sym"]
			sym_table[symbol["val"]] = {
				"enter" : i
			}
			# find out where this exits, by finding last reference
			exit = -1
			for j in reversed(range(len(actions))):
				if action_references_symbol(actions[j], symbol, DEBUG=DEBUG):
					sym_table[symbol["val"]]["exit"] = j
					exit = j
					break
			# if i == j, then the result of the expression is unused.
			action["unused"] = (i == j) or (exit == -1)
			if action["unused"]: sym_table[symbol["val"]]["exit"] = i
	return sym_table