#!/usr/bin/python

from process import processAST, ROPSyntaxError
from flatten import flatten
from validate import validate
from analyze import generateSymTable, propogateConstants
from ropcompile import precompile_payload, compile_payload, ROPCompilationError
from gadgets import gadgets
from copy import deepcopy
from tests import run_test_suite
from gracoparser import CropParser
from symbols import *

import os
import sys

def printUsage():
	print "usage: {} <program> <binary> [--verbose | -v] [--test | -t]".format(sys.argv[0])
	print "program: a program written in crop, to be compiled."
	print "binary: an ELF, linux x86 binary to attack."
	print "Optional Arguments -"
	print "[v]erbose: Enter verbose mode, for debugging."
	print "[t]est: Run the test suite."

def main(args):

	DEBUG = "--verbose" in args or "-v" in args
	if DEBUG:
		idx = args.index("--verbose") if "--verbose" in args else args.index("-v")
		del args[idx]
	RUN_TESTS = "--test" in args or "-t" in args
	if RUN_TESTS:
		idx = args.index("--test") if "--test" in args else args.index("-t")
		del args[idx]

	if len(args) != 2:
		printUsage()
		return

	if RUN_TESTS:
		# TODO: Run test suite.
		print "crop: Test Suite"
		print "------------------"
		run_test_suite()
		print "------------------"
	else:
		BUFFER_ADDR = 0xb77ff300
		print "[info] Buffer located at {}".format(BUFFER_ADDR)

		# Regular mode.
		corpus = args[0]
		fname = args[1]
		
		# Load Text
		with open(corpus, "r") as f:
			corpus = f.read()

		# Process Text into program actions.
		try:
			# Tokenize text using the grako parser.
			parser = CropParser()
			ast = parser.parse(corpus)
			print "[+] Parser finished."


			# Process tokens -> actions. First pass.
			actions = processAST(ast)
			print "[+] Lexer finished."

			if DEBUG:
				print "---Stage 1 Compilation---"
				for action in actions:
					print rts(action)
				print "------------------------------"

			validate(actions)
			print "[+] Validator finished."

			flattening = True

			while flattening:
				# Propogate Constants
				actions = propogateConstants(actions, DEBUG=True)
				print "[-] Analyzer propogated constants..."
				# Flatten actions to optimize them.
				actions, flattening = flatten(actions, optimize=True, DEBUG=False)
				print "[-] Flattened"
			print "Flattening done."
			print "Final propogation: "
			actions = propogateConstants(actions, DEBUG=True)

			if DEBUG:
				print ""
				print "---Stage 2 Compilation---"
				for action in actions:
					print rts(action)
				print "------------------------------"


			# Analyze for variable lifetimes.
			sym_table = generateSymTable(actions, DEBUG=DEBUG)
			print "[+] Analyzer generated Symbol Table"

			if DEBUG:
				print "## Sym table ##"
				for symbol in sym_table:
					print "# {} -> ({}, {})".format(symbol, sym_table[symbol]["enter"], sym_table[symbol]["exit"])
				print "###############"

			for action in actions:
				if "unused" in action and action["unused"] and not "constant" in action:
					print "[analyzer] Warning: variable '{}' unused.".format(action["sym"]["val"])
			if DEBUG:
				print "---Stage 3 Compilation---"
				for action in actions:
					print rts(action)
				print "------------------------------"
		except ROPSyntaxError as e:
			print e
			return

		try:
			# Given the actions, find ROP sequences that satisfy these actions.
			sequences = None
			payload = precompile_payload(actions, sym_table, sequences, DEBUG=DEBUG)
			if DEBUG:
				printStackPayload(payload)
			print "[+] Payload Generation: Precompiled payload. "

			# load the gadgets from the binary.
			print "[-] ropgadget: Loading gadgets..."
			binary_gadgets = gadgets(fname)
			num_gadgets_total = sum([len(binary_gadgets[k]) for k in binary_gadgets])
			
			print "[+] ropgadget: Loaded gadgets from \"{}\" (got {})".format(fname, num_gadgets_total)
			
			# compile the actual payload.
			full_payload = compile_payload(payload, binary_gadgets, BUFFER_ADDR, DEBUG=DEBUG)
			print "[+] Compiled final payload."

			if DEBUG:
				printStackPayload(payload)
		except ROPCompilationError as e:
			print e
			return

if __name__ == "__main__":
	main(sys.argv[1:])