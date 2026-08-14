# Cattykit

Cattykit is a framework for implementing artificial intelligence models based on components from the cognitive models of the Fluid Analogies Research Group including a shared workspace, slipnet, coderack, and codelets.

## Usage

To install and run a model once on a single problem:

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

To run a suite of problems on a single model:

``` python
from cattykit import install_model, run_experiment

# Install the model if necessary.
cattykit.install_model("./models/copycat")

results_db = run_experiment(
    model_name="copycat",
    problems=[
	    "abc -> abd ==> ijk -> ?",
		"abc -> abc ==> iijjkk -> ?",
		"abc -> abc ==> kji -> ?",
		"abc -> abc ==> mrrjjj -> ?",
		"abc -> abc ==> xyz -> ?",
    ],
	iterations=1000
)
print(results_db)
```

This will generate a database located at `results_db` containing logs of the runs and summary statistics. These can be explored using the Cattycam package.
