#!/usr/bin/env python2
## -*- coding: utf-8 -*-
##
##  Justin Brower - 2017-04-14
## 	Brown University

import re
from   capstone import *



class ROPMakerCFIX86(ROPMaker):
    def _generate():
    	# TODO: generate payload.
    	print "Part 1: Function Calling Primitive"
    	print "----------------------------------"
    	function_calling_primitives = self.__findFunctionCallingPrimitive()

    	print "Part 2: Null-Byte Writing Primitive"
    	print "----------------------------------"

    	print "Part 3: Sys-Call Primitive."
    	print "----------------------------------"
    	pass

    def __named_register_groupre(self, name):
    	return "(?P<{}>([(eax)|(ebx)|(ecx)|(edx)|(esi)|(edi)]{3}))".format(name)


    def __getGadgetSideEffects():


    def __findFunctionCallingPrimitive(self):
    	'''
    	Returns a call-ret pair, for use with the compiler.
    	'''
    	# Step 1: Find register call gadget.
    	availableRegisterCallGadgets = []	

    	for gadget in self.__gadgets:
    		g = gadget["gadget"].split(" ; ")
    		regex = re.search("call {}".format(self.__named_register_groupre('reg')), g)
    		if regex:
    			# Relative call gadget found. No control flow transfers allowed in these gadgets.
    			if not "jmp" in gadget["gadget"]:
    				print "Found register call gadget targeting {}: {}".format(regex.group('reg'), g)
    				availableRegisterCallGadgets.append((regex.group('reg'), gadget))

    	if not availableRegisterCallGadgets:
    		print "No register call gadgets were available. You'll need to find another way to call a function."
    		return []

    	# Step 2: Find register loading gadgets, to set stage for 
    	availableRegisterLoadGadgets = []
    	for gadget in self.__gadgets:
    		g = gadget["gadget"].split(" ; ")

    		regex = re.search("pop {}".format(self.__named_register_groupre('reg')), g)
    		if regex:
    			# Relative call gadget found. No control flow transfers allowed in these gadgets.
    			if not "jmp" in gadget["gadget"]:
    				print "Found register load gadget for {}: {}".format(regex.group('reg'), g)
    				availableRegisterLoadGadgets.append((regex.group('reg'), gadget))


    	if not availableRegisterLoadGadgets:
    		print "No register loads were available."
    		return []





