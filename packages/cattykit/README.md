# Cattykit

Cattykit (in development) is a framework for implementing artificial intelligence models based on components from the cognitive models of the Fluid Analogies Research Group described in Hofstadter _et al_ 1995. Their models are typically built with similar components, including: a shared _workspace_, _slipnet_, _coderack_, and _codelets_.

Models solve problems represented by graph-like structures in a workspace which is incrementally edited by micro-agents called _codelets_ that propose, build, and destroy new structures. The _slipnet_ keeps track of concepts relevant to the structures present in the workspace and encourages codelets that continue their construction. The _coderack_ is a stochastic scheduler of codelets, which are selected according to urgency. All processes in each model occur with a degree of randomness mediated by its _temperature_ which (unlike the related concept used in language model decoding and simulated annealing) is a measure of workspace quality constantly adjusted by the model itself.

This repository was initially motivated by the lack of a common software framework for FARG models, which were typically developed as isolated projects, often using different programming languages (some of which are now obsolete). This hinders further research into the models and, despite the promise they show as an approach to symbolic AI, acts as a barrier to their adoption in AI more widely.

## Installation

Install with pip:

``` bash
pip install cattykit
```

## Quick start

Start by installing a model in your environment (this requires pip in the local environment).

``` python
import cattykit

# providing a name will install the model from the Cattykit repository
cattykit.install_model("copycat")

print(cattykit.available_models())
# ('cattykit',)

# providing a uri will install a model from your computer or elsewhere
cattykit.install_model("path/to/model")
```

Once you have installed a model, you can ask it to solve a problem.

```python
import cattykit

copycat = cattykit.load_model("copycat", config={"seed": 1234})

result = copycat.solve("abc -> abd ==> ijk -> ?")

print(result)
# 'ijl'
```

## References

* Hofstadter, D. R., et al. (1995). Fluid Concepts and Creative Analogies: Computer Models of the Fundamental Mechanisms of Thought. Basic Books. [doi:10.5555/218753](https://dl.acm.org/doi/10.5555/218753)
* Mitchell, M (1993). Analogy-Making as Perception: A Computer Model. The MIT Press. [doi:10.5555/152203](https://dl.acm.org/doi/book/10.5555/152203)

## License

Cattykit is licensed under the GNU Affero General Public License v3.0 or later.
See [LICENSE](LICENSE) for details.
