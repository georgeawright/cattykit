# \[Re\] Copycat: a Replication of the Classic Model of Analogy-Making

George Alexander Wright

## Abstract

Copycat is a stochastic computer model of analogy-making developed by
Mitchell \[@Mitchell1993\]. It solves analogies on strings via a large
number of codelets operating in a shared workspace and uses a
temperature score to rate workspace quality and modulate its own degree
of randomness. Copycat became influential within certain branches of
cognitive science and artificial intelligence, but further study of it
is constrained by the difficulty of running its original Lisp
implementation on contemporary computers. This paper presents a
replication study of Mitchell’s \[@Mitchell1993\] published experiments
on Copycat involving 1,000 runs on each of a set of 29 analogy problems,
using a Python re-implementation of the model. The re-implementation’s
overall answer distributions, mean final temperature scores per answer,
and mean run length per problem are close to the originally reported
values (the mean empirical overlap in answer distributions is 97.9%;
mean absolute error in temperature scores weighted by answer frequency
is 0.005; and mean relative error in codelets run is 0.033). This
re-implementation permits further analysis of the model including: a
statistical analysis of the effects of increasing the precision of the
temperature score and other internal numerical values; and an analysis
of the handling of so-called snags. The re-implementation also provides
a basis for further study and extension of Copycat and related
architectures.

## Cite this paper

``` bibtex
@misc{wright2026copycat-replication,
  author = {George Alexander Wright},
  title = {[Re] Copycat: a Replication of the Classic Model of Analogy-Making},
  url = {https://github.com/georgeawright/cattykit/tree/main/papers/copycat-reproduction},
  year = {2026},
}
```
