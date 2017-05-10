import ropgadget
from ropgadget.binary import Binary
from ropgadget.options import Options
from ropgadget.args import Args
from ropgadget.gadgets import Gadgets
from ropgadget.core import Core
import re

def mkgadget(vaddr, gtype):
	return {"vaddr" : vaddr, "type" : gtype}

def esp_lift(vaddr, amount, affected_regs, roplen):
	g = mkgadget(vaddr, "ESP_LFT")
	g["REGS"] = affected_regs
	g["LEN"] = roplen
	g["AMT"] = amount
	return g

def reg_load_stck(vaddr, affected_regs, roplen):
	'''
	Gadget which allows loading registers from stack.
	'''
	g = mkgadget(vaddr, "REG_LOAD_MEM")
	g["REGS"] = affected_regs
	g["LEN"] = roplen
	return g

def reg_write_mem(vaddr, affected_regs, affected_mem, roplen):
	'''
	Gadget to write from register -> memory.
	'''
	g = mkgadget(vaddr, "REG_LOAD_MEM")
	g["REGS"] = affected_regs
	g["WHERE"] = affected_mem
	g["LEN"] = roplen
	return g

def findAffectedRegisters(disasm):
	instrs = disasm.split(";")
	regs = r"(eax|esi|edi|esp|ebx|ebp|edx|ecx)"
	return re.findall(regs, disasm)

P_IS_REG_LOAD = r"pop (eax|esi|edi|esp|ebx|ebp|edx|ecx)"
P_ADD = r"add"
P_SUB = r"sub"
P_ESP_LFT = r"(add esp)|(pop)"

P_MEM_WRITE = r"mov (?P<amt>[d|q]word|word|byte) ptr (?P<from>\[(eax|esi|edi|esp|ebx|ebp|edx|ecx)\]), (?P<to>eax|esi|edi|esp|ebx|ebp|edx|ecx)"
P_MEM_READ = r"mov (?P<to>eax|esi|edi|esp|ebx|ebp|edx|ecx), (?P<amt>[d|q]word|word|byte) ptr (?P<from>\[(eax|esi|edi|esp|ebx|ebp|edx|ecx)\])"

TYPES = {
	"reg_load" : lambda disasm: re.search(P_IS_REG_LOAD, disasm),		# gadgets to load reg from stack
	"add" : lambda disasm: re.search(P_ADD, disasm),									# gadgets to perform addition on register
	"sub" :  lambda disasm: re.search(P_SUB, disasm),									# gadgets to perform subtraction on register
	"esp_lift" : lambda disasm: re.search(P_ESP_LFT, disasm),								# gadgets to lift ESP
	"mem_read" :  lambda disasm: re.search(P_MEM_READ, disasm),								# gadgets to read word from memory into reg
	"mem_write" : lambda disasm: re.search(P_MEM_WRITE, disasm),								# gadgets to write word from reg into memory.
	"other" : lambda disasm: True
}

def parseEspLift(disasm, data):
	# count number of pops.
	# count amount added to esp
	numPops = re.findall(r"pop", disasm)
	espAdds = re.findall(r"add esp, (?P<amt>0x[a-fA-F0-9]+)", disasm)

	data["AMT"] = len(numPops)
	data["REGS"] = findAffectedRegisters(disasm)
	if espAdds:
		data["AMT"] += sum(map(lambda ref: int(ref, 16), espAdds))

def parseMemOp(disasm, data):
	writes = re.finditer(P_MEM_WRITE, disasm)
	for write in writes:
		reg = write.group('to')
		from_reg = write.group('from')
		amt = write.group('amt')
		if not "LOAD" in data or not data["LOAD"]: data["LOAD"] = set()
		data["LOAD"].add((from_reg, reg)) # indicating reading or writing from reg -> reg
		data["AMT"] = amt


PARSERS = {
	"reg_load" : lambda disasm, data: re.search(P_IS_REG_LOAD, disasm),		# gadgets to load reg from stack
	"add" : lambda disasm, data: re.search(P_ADD, disasm),									# gadgets to perform addition on register
	"sub" :  lambda disasm, data: re.search(P_SUB, disasm),									# gadgets to perform subtraction on register
	"esp_lift" : parseEspLift,								# gadgets to lift ESP
	"mem_read" :  parseMemOp,								# gadgets to read word from memory into reg
	"mem_write" : parseMemOp,								# gadgets to write word from reg into memory.
	"other" : lambda disasm, data: True
}

def classifyGadget(gadget):
	'''
	{'gadget': 
		u'xor dword ptr [edx], 0x2b ; add byte ptr [eax], al ; ret', 
	 'prev': '\x0f\x08[=\x01\xf0\xff\xff\x0f', 
	 'bytes': '\x832+\x00\x00\xc3', 
	 'decodes': <generator object disasm at 0x102757c30>, 
	 'vaddr': 134568009L}
	'''
	gadget["REGS"] = findAffectedRegisters(gadget["gadget"])
	if not "types" in gadget: gadget["types"] = []
	for key in TYPES:
		validator = TYPES[key]
		if validator(gadget["gadget"]): 
			gadget["types"].append(key)
			PARSERS[key](gadget["gadget"], gadget)
	return gadget["types"]

def gadgets(path):
	# TODO: Use ROPGadget to load gadgets from the binary in path
	args = ["--binary", path, "--callPreceded"]
	ropcore = Core(Args(args).getArgs())
	all_gadgets = ropcore.getGadgetsQuiet()
	print "ropgadget provided {} gadgets.".format(len(all_gadgets))
	gadgets = {
		"reg_load" : [],	# gadgets to load reg from stack
		"add" :  [],			# gadgets to perform addition on register
		"sub" :  [],			# gadgets to perform subtraction on register
		"esp_lift" :  [],	# gadgets to lift ESP
		"mem_read" :  [],	# gadgets to read word from memory into reg
		"mem_write" :  [],	# gadgets to write word from reg into memory.
		"other" :  []
	}

	for gadget in all_gadgets:
		gtypes = classifyGadget(gadget)
		for gtype in gtypes:
			gadgets[gtype].append(gadget)
	print "----Gadget Types Loaded----"
	for key in gadgets:
		print "{}: {} gadgets".format(key, len(gadgets[key]))
	print "---------------------------"
	print_gadgets_from = "mem_write"
	for gadget in gadgets[print_gadgets_from]:
		print "{}\n writing ability: {}\n".format(gadget["gadget"],gadget["LOAD"])
	assert False
	return gadgets