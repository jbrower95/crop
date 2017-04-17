from process import process, ROPSyntaxError
from tokenize import tokenize
from flatten import flatten
from ropcompile import ropcompile
from grammar import grammar

import os
import sys

def main(args):
	corpus = args[0]
	fname = corpus
	
	# Load Text
	with open(corpus, "r") as f:
		corpus = f.read()

	# Tokenize text
	tokens = tokenize(corpus, grammar)

	# Process Text into program actions.
	try:
		actions = process(tokens, corpus)
		for action in actions:
			print action
	except ROPSyntaxError as e:
		print e
		return

	# Flatten actions to optimize them.
	actions = flatten(actions, optimize=True)

	# Given the actions, find ROP sequences that satisfy these actions.
	sequences = None
	payload = ropcompile(actions, sequences)
	print payload

if __name__ == "__main__":
	main(sys.argv[1:])