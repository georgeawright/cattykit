# Papers

This directory contains articles that relate to the work in this repository.
Articles are authored in [Quarto Markdown](https://quarto.org/docs/authoring/).
The paper build creates GitHub Flavored Markdown for repository browsing, and
LaTeX which is compiled into a PDF. Quarto handles citations, bibliography
generation, figure/table captions, and cross-references for both outputs.

Each paper directory contains a `paper.qmd` source document. Do not edit the
generated `paper.md`, `README.md`, or `paper.tex`; make changes in `paper.qmd`
and rebuild.

Use Quarto's cross-reference syntax for labelled figures and tables:

``` markdown
![A useful figure caption.](figures/example.png){#fig-example}

As shown in @fig-example, ...

| Measure | Value |
|:--------|------:|
| Result  |  1.23 |

: A useful table caption. {#tbl-example}

See @tbl-example for the result.
```

Quarto processes `[@citation-key]` citations using the paper's bibliography and
adds a formatted `References` section to both the generated Markdown and PDF.

The QMD front matter also has a `bibtex` block. It produces a concise generated
`README.md` containing the title, abstract, and a copyable BibTeX citation.
`author` and `title` are inherited from the standard QMD metadata; the entry
`type` and `fields` supply any remaining BibTeX metadata:

``` yaml
bibtex:
  type: inproceedings
  key: wright2027example
  fields:
    booktitle: "Proceedings of ExampleConf"
    pages: "1--12"
    year: "2027"
```

## Reusable table fragments

Store a table in `tables/name.md`, including its caption and Quarto table label,
then include it where it belongs in `paper.qmd`:

``` markdown
{{< include tables/name.md >}}
```

The include directive must be on its own line with blank lines around it. It is
expanded before rendering, so its table, caption, label, and citations appear
in both output formats. The paper Makefile treats `tables/*.md` as inputs, so a
table change automatically triggers a rebuild.

## Building a paper

To generate `paper.md` (the full GitHub Flavored Markdown manuscript),
`README.md` (title, abstract, and citation), and `paper.pdf`, run this command
from inside this directory:

``` bash
make PAPER=directory-name
```

Replace `directory-name` with the name of the directory that contains a `paper.qmd` file.

The build requires [Quarto](https://quarto.org/docs/get-started/) and a LaTeX
installation that provides `latexmk`. Individual outputs can be generated with
`make PAPER=directory-name markdown`, `readme`, `latex`, or `pdf`.

## License

Unless otherwise indicated, the manuscript texts and original figures in the
sub-directories of this directory are licensed under the Creative Commons Attribution
4.0 International License (CC BY 4.0). Third-party material remains subject to its
respective copyright and licence terms.
