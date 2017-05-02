#!/usr/bin/env python2
## -*- coding: utf-8 -*-
##
##  Justin Brower - 2017-04-14
## 	Brown University

import re
from   capstone import *
from collections import defaultdict

class ROPMaker:
	def __init__(self, binary, gadgets, liboffset=0x0):
		# Running Values of allocated registers. 
    	self.__clear()

    	self.__binary  = binary
        self.__gadgets = gadgets
        # If it's a library, we have the option to add an offset to the addresses
        self.__liboffset = liboffset
    	self.__gadgets.reverse() # Smallest gadgets first.
        self.__generate()

    def _setRegister(self, register, value, useBlacklist=True):
    	'''
    	Sets the value of a register in this compilation sequence.

    	returns True if the action took place, otherwise false.
    	'''
    	if {register: value} in self.__deadends[-1]:
    		# Dead end.
    		print "[ropmaker] Set register ({}=>{}) blocked: previously rolled this back.".format(register, value)
    		return False
    	self.__registers.append(dict(self.__registers[-1], **{register: value, "__delta" : {register: value}}))
    	self.__deadends.append({}) # no known dead-ends.
    	return True

    def _rollback(self, blacklist=True):
    	'''
    	If a sequence is unsatisfiable, rolls back the sequence. 

    	Returns number of sequences rolled back
    	'''
    	if self.__registers: 
    		bad_state, _ = self.__registers.pop(), self.__deadends.pop()
    		if blacklist:
    			# prevent this change again.
    			print "[ropmaker] Rolled back {}, added to blacklist.".format(str(bad_state["__delta"]))
    			self.__deadends[-1].add(bad_state["__delta"])

    def _clear(self):
    	'''
    	Clear all compilation memory.
    	'''
    	self.__registers = [{}]
    	self.__deadends = []

    def _currentRegisters(self):
    	'''
    	Returns the current registers.
    	'''
    	return self.__registers[-1]

    def _generate(self):
    	# implement in subclasses.
    	pass