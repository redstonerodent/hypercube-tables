v ?=
.PHONY: all-pdf all-tex clean default
default: clean all-tex
all-tex: $(patsubst %.tsv, %.tex, $(wildcard *.tsv))
all-pdf: $(patsubst %.tsv, %.pdf, $(wildcard *.tsv))
clean:
	-rm *.pdf
	-rm *.tex

%.tex: %.tsv
	python hypercube.py $< $(v) > $@

%.pdf: %.tex
	tectonic $<

