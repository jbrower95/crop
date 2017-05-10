grammar: crop.graco
	echo "Building Grammar..."
	grako crop.graco -n -m Crop --generate-parser --outfile parser.py
	cp parser.py ../gracoparser.py

test: grammar
	python parser.py ../samples/sample.rop
