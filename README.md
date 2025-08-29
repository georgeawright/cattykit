# Resurrected Copycat

This is a port into Python 3 of the classic model of analogy making Copycat. The source code for the original version of Copycat was written in a version of Common Lisp that is not compatible with modern implementations.

The original lisp source code of Copycat can be found [here](https://melaniemitchell.me/ExplorationsContent/how-to-get-copycat.html).

This version of Copycat is written in an object-oriented style, with each of the major components (workspace, slipnet, coderack) as well as all workspace structures, slipnet nodes and links, and codelets treated as objects.

# Overview of the Copycat Architecture

## Codelets

When a codelet runs, it makes a small change to the workspace and then posts a follow-up codelet to the coderack.

Codelets run in chains with each type of codelet having a particular type of follow-up:

Scout -> StrengthTester -> Builder


