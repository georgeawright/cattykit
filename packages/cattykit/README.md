# Cattykit

Cattykit is a framework for implementing artificial intelligence models based on components from the cognitive models of the Fluid Analogies Research Group including a shared workspace, slipnet, coderack, and codelets.

## Usage

```python
import cattykit
from cattykit.logging import PrintLogger

# Install a model package once. The source can also be a model name or HTTPS URL.
cattykit.install_model("./models/copycat")

print(cattykit.available_models())
# ("copycat",)

logger = PrintLogger()
try:
    copycat = cattykit.load_model(
        "copycat",
        config={"seed": 1234},
        logger=logger,
    )
    copycat.solve("abc -> abd ==> ijk -> ?")
finally:
    logger.close()
```
