import os
import sys

def enumerateTests(indir):
	try:
		test_dir = "tests/{}".format(indir)
		files = os.listdir(test_dir)
		return set([f.split(".")[0] for f in files])
	except OSError as e:
		print "[test-suite] Error enumerating tests in {}: {}".format(indir, e) 

def run_test_suite():
	print "[test-suite] Testing tokenizer..."
	tests = enumerateTests("tokenizer")
	
	print "[test-suite] Testing processor..."
	tests = enumerateTests("process")

	print "[test-suite] Testing flattener..."
	tests = enumerateTests("flatten")

	print "[test-suite] Testing compiler..."
	tests = enumerateTests("ropcompile")



def test_tokenizer(tests):
	pass

def test_process(tests):
	pass

def test_flatten(tests):
	pass

def test_ropcompile(tests):
	pass