from process import ROPSyntaxError
from symbols import *
from primitives import primitives

DEBUG = True

def validate(actions):
	# one, global scope.
	scope = set()
	
	# add all primitive functions.
	for region in primitives:
		scope.update((primitives[region].keys()))

	for action in actions:
		if action["action"] == "bind":
			# Bind affects scope, so handle here.
			validate_rval(action["rvalue"], scope)
			# Assuming the rvalue here is OK, add this binding to scope.
			scope.add(action["sym"]["val"])
		else:
			# Validate the action as an rval.
			validate_rval(action, scope)

def validate_rval(action, scope):
	if action["type"] == "action" and action["action"] == "apply":
		# Validate function name
		throwIfAbsent(action, scope)
		for argument in action["args"]:
			validate_rval(argument, scope)
	elif action["type"] == "sym":
		throwIfAbsent(action, scope)

def throwIfAbsent(action, scope):
	if action["type"] == "sym" or (action["type"] == "action" and action["action"] == "apply"):
		if "sym" in action and not action["sym"]["val"] in scope:
			raise ROPSyntaxError("Unknown symbol '{}'.".format(rts(action["sym"])), action["loc"])
