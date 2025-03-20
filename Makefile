.PHONY: all test plumber tetrotile tcells asp-cgs

all: test plumber tetrotile tcells asp-cgs

test:
	./go.sh test

plumber:
	./go.sh plumber

tetrotile:
	./go.sh tetrotile

tcells:
	./go.sh tcells

asp-cgs:
	./go.sh asp-cgs
