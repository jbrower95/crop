from collections import OrderedDict
import re


def tokenize(corpus, grammar):
	# Load tokens, in order.
	all_tokens = grammar["tokens"]
	collected_tokens = {}

	# Parse all tokens, in order, replacing them with escaped sequences.
	for token in all_tokens:
		# print "Processing token: " + str(token)
		for match in re.finditer(token["regex"], corpus):
			if match.start() not in collected_tokens:
				value = match.group()
				if "transform" in token:
					# a way to parse these values has been defined. use it
					value = token["transform"](value)
				# store token data
				collected_tokens[match.start()] = {"name" : token["name"], "value" : match.group()}
	collected_tokens[len(corpus)] = {"name" : "EOF", "value" : "<end>"}
	print "[+] Tokenizer finished."
	return OrderedDict(sorted(collected_tokens.items(), key=lambda t: t[0]))


