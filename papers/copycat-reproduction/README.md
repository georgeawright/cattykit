# Reproducing Copycat: a Python Re-implementation of a Classic Model of Analogy-Making

## Abstract

Copycat is a stochastic computer model of analogy-making developed by
the Fluid Analogies Research Group. Its original Common Lisp
implementation is difficult to run in contemporary environments,
limiting further study of the architecture. This paper presents a Python
re-implementation and compares its behaviour with published results for
29 analogy problems, using 1,000 runs per problem. The modal answer
agrees with the published result for all 29 problems, and the overall
answer distributions and mean final temperature scores are close to
published values. Agreement in mean run length is weaker and varies
across problems, with a mean relative error of 7.1%. A variant using
two-decimal numerical quantization has a mean relative error of 3.3%,
suggesting that numerical representation affects Copycat’s search
effort. This re-implementation permits analysis of the occurrence and
handling of snags, which are strongly associated with longer runs. The
re-implementation also provides a basis for further study and extension
of Copycat and related architectures and marks the first step in a
research programme aimed at a general library for constructing and
studying such architectures.

## Cite this paper

``` bibtex
@misc{wright2026copycat-reproduction,
  author = {George Alexander Wright},
  title = {Reproducing Copycat: a Python Re-implementation of a Classic Model of Analogy-Making},
  url = {https://github.com/georgeawright/cattykit/tree/main/papers/copycat-reproduction},
  year = {2026},
}
```
