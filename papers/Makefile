PAPER ?=

ifeq ($(PAPER),)
$(error PAPER is not set. Use: make PAPER=copycat-reproduction)
endif

DIR = $(PAPER)
QMD = $(DIR)/paper.qmd
MD = $(DIR)/paper.md
README = $(DIR)/README.md
TEX = $(DIR)/paper.tex
PDF = $(DIR)/paper.pdf

QUARTO = quarto
LATEXMK = latexmk

FIGURES = $(wildcard $(DIR)/figures/*)
TABLES = $(wildcard $(DIR)/tables/*.md)
README_FILTER = readme.lua
README_TEMPLATE = readme-template.md

.PHONY: all markdown readme latex pdf clean

all: $(MD) $(README) $(PDF)

markdown: $(MD)

readme: $(README)

latex: $(TEX)

pdf: $(PDF)

$(MD): $(QMD) references.bib $(FIGURES) $(TABLES)
	$(QUARTO) render $(QMD) --to gfm

$(README): $(QMD) $(README_FILTER) $(README_TEMPLATE)
	cd $(DIR) && $(QUARTO) render paper.qmd --to gfm --output README.md -M render-readme:true --template ../$(README_TEMPLATE)

$(TEX): $(QMD) references.bib $(FIGURES) $(TABLES)
	$(QUARTO) render $(QMD) --to latex

$(PDF): $(TEX) $(FIGURES)
	cd $(DIR) && $(LATEXMK) -pdf paper.tex

clean:
	cd $(DIR) && $(LATEXMK) -C paper.tex
	rm -f $(MD) $(README) $(TEX)
