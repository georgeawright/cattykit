# Cattykit

Cattykit (in development) is a framework for implementing artificial intelligence models based on components from the cognitive models of the Fluid Analogies Research Group described in Hofstadter _et al_ 1995. Their models are typically built with similar components, including: a shared _workspace_, _slipnet_, _coderack_, and _codelets_.

Models solve problems represented by graph-like structures in a workspace which is incrementally edited by micro-agents called _codelets_ that propose, build, and destroy new structures. The _slipnet_ keeps track of concepts relevant to the structures present in the workspace and encourages codelets that continue their construction. The _coderack_ is a stochastic scheduler of codelets, which are selected according to urgency. All processes in each model occur with a degree of randomness mediated by its _temperature_ which (unlike the related concept used in language model decoding and simulated annealing) is a measure of workspace quality constantly adjusted by the model itself.

This repository was initially motivated by the lack of a common software framework for FARG models, which were typically developed as isolated projects, often using different programming languages (some of which are now obsolete). This hinders further research into the models and, despite the promise they show as an approach to symbolic AI, acts as a barrier to their adoption in AI more widely.

## Status

This project is in a state of active development and its APIs may change.

Currently, work is focused on a faithful reproduction of Copycat, a model of analogy making on string problems. The version of Copycat in this repository runs end-to-end, but some discrepancies remain between the distribution of solutions that it produces and the distribution reported in Mitchell 1993.

## Repository structure

This repository hosts the packages:

* **Cattykit** a general purpose library for developing and testing models
* **Cattycam** a web-app based tool for viewing the internal structures and processes in Cattykit models and debugging models in development

This repository also hosts model implementations:

* **Copycat** a reproduction of the original FARG model which solves analogies between strings, translated from the [original Lisp source](https://melaniemitchell.me/ExplorationsContent/how-to-get-copycat.html) and following the description in Mitchell 1993.

## Installation

Clone the latest source code:

``` bash
git clone https://github.com/georgeawright/cattykit.git
```

To install the Cattykit library, run:

``` bash
cd /path/to/repo/packages/cattykit
pip install -e .
```

To install the Cattycam web-app, run:

``` bash
cd /path/to/repo/packages/cattycam
pip install -e .
```

## Quick start

To install a model and run it on a single problem:

```python
from cattykit import install_model, load_model

install_model("copycat")
copycat = load_model("copycat", config={"seed": 1234})

copycat.solve("abc -> abd ==> ijk -> ?")
```

For more detailed examples see the [`examples`](examples/) directory.

## References

* Hofstadter, D. R., et al. (1995). Fluid Concepts and Creative Analogies: Computer Models of the Fundamental Mechanisms of Thought. Basic Books. [doi:10.5555/218753](https://dl.acm.org/doi/10.5555/218753)
* Mitchell, M (1993). Analogy-Making as Perception: A Computer Model. The MIT Press. [doi:10.5555/152203](https://dl.acm.org/doi/book/10.5555/152203)

## License

Cattykit is licensed under the GNU Affero General Public License v3.0 or later.
See [LICENSE](LICENSE) for details.
