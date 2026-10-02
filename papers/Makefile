PAPER ?=

ifeq ($(PAPER),)
$(error PAPER is not set. Use: make PAPER=copycat-reproduction)
endif

DIR = $(PAPER)
MD = $(DIR)/paper.md
META = $(DIR)/metadata.yaml
TEX = $(DIR)/paper.tex
PDF = $(DIR)/paper.pdf

PANDOC = pandoc
LATEXMK = latexmk

FIGURES = $(wildcard $(DIR)/figures/*)

.PHONY: all clean

all: $(PDF)

$(TEX): $(MD) $(META) references.bib $(FIGURES)
	$(PANDOC) $(META) $(MD) \
		--citeproc \
		-o $(TEX)

$(PDF): $(TEX) $(FIGURES)
	cd $(DIR) && $(LATEXMK) -pdf paper.tex

clean:
	cd $(DIR) && $(LATEXMK) -C paper.tex
	rm -f $(TEX)
