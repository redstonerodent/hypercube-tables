v ?=
d ?= .
.PHONY: all-pdf all-tex clean default
default: clean all-tex
all-tex: $(patsubst $(d)/%.tsv, $(d)/%.tex, $(wildcard $(d)/*.tsv))
all-pdf: $(patsubst $(d)/%.tsv, $(d)/%.pdf, $(wildcard $(d)/*.tsv))
clean:
	rm -f $(d)/*.pdf
	rm -f $(d)/*.tex

%.tex: %.tsv
	python hypercube.py $< $(v) > $@

%.pdf: %.tex
	tectonic $<

