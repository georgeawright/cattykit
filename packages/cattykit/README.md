# Cattykit

Cattykit is a framework for implementing artificial intelligence models based on components from the cognitive models of the Fluid Analogies Research Group including a shared workspace, slipnet, coderack, and codelets.

## Usage

``` Python
import cattykit

print(cattykit.available_models())

copycat = cattykit.load_model(
    "copycat",
    config={"seed": 1234},
)
result = copycat.solve("abc -> abd ==> ijk -> ?")
```
