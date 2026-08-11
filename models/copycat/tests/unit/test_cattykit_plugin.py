from cattykit.logging import ModelEvent
from cattykit.models import CattyKitModel
from copycat.cattykit_plugin import create_model, plugin


def test_copycat_plugin_exposes_the_cattykit_model_descriptor() -> None:
    descriptor = plugin()

    assert descriptor.name == "copycat"
    assert descriptor.version == "0.1.0"


def test_copycat_factory_returns_a_cattykit_model() -> None:
    logger = RecordingLogger()
    model = create_model(config={"seed": 1234}, logger=logger)

    assert isinstance(model, CattyKitModel)
    assert model.logger is logger


class RecordingLogger:
    def __init__(self) -> None:
        self.events: list[ModelEvent] = []

    def log(self, event: ModelEvent) -> None:
        self.events.append(event)

    def close(self) -> None:
        pass
