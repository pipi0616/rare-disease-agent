"""The skeleton has one behaviour: the entry point runs and says hello."""

import pytest

from raredx import main


def test_main_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    assert capsys.readouterr().out.strip() == "Hello from raredx!"
