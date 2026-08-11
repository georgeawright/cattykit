from cattykit.models import CattyKitModel
from copycat.cattykit_plugin import create_model, plugin


def test_copycat_plugin_exposes_the_cattykit_model_descriptor() -> None:
    descriptor = plugin()

    assert descriptor.name == "copycat"
    assert descriptor.version == "0.1.0"


def test_copycat_factory_returns_a_cattykit_model() -> None:
    model = create_model(config={"seed": 1234})

    assert isinstance(model, CattyKitModel)
