grammar: grammar/crop.graco
	cd grammar && make
debug: grammar
	python main.py samples/sample.rop binaries/Elf-Linux-x86
all: grammar
	python main.py samples/sample.rop binaries/Elf-Linux-x86 --verbose




