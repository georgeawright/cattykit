from unittest.mock import patch

import pytest
from cattykit.cli import main
from cattykit.models import ModelSourceError


@patch("cattykit.cli.install_model")
def test_install_command_passes_model_and_version_to_installer(
    install_model: object,
) -> None:
    main(["install", "copycat", "--version", "0.1.0"])

    install_model.assert_called_once_with("copycat", version="0.1.0")  # type: ignore[attr-defined]


@patch("cattykit.cli.install_model", side_effect=ModelSourceError("not found"))
def test_install_command_reports_installation_errors(install_model: object) -> None:
    with pytest.raises(SystemExit, match="2"):
        main(["install", "missing"])

    install_model.assert_called_once_with("missing", version=None)  # type: ignore[attr-defined]
