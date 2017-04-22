

def gadgets(path):
	# TODO: Use ROPGadget to load gadgets from the binary in path.
	return {
		"reg_load" : [],	# gadgets to load reg from stack
		"add" : [],			# gadgets to perform addition on register
		"sub" : [],			# gadgets to perform subtraction on register
		"esp_lift" : [],	# gadgets to lift ESP
		"mem_read" : [],	# gadgets to read word from memory into reg
		"mem_write" : []	# gadgets to write word from reg into memory.
	}