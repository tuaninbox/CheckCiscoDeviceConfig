import pytest
from core.device import ConfigSanitizer

def test_remove_token_with_env():
    sanitizer = ConfigSanitizer()
    config = "run-opt --env TEAGENT_ACCOUNT_TOKEN=abcd1234"
    expected = "run-opt --env TEAGENT_ACCOUNT_TOKEN=<removed>"
    assert sanitizer.remove_app_hosting(config) == expected

def test_remove_token_with_short_e():
    sanitizer = ConfigSanitizer()
    config = "run-opt -e TEAGENT_ACCOUNT_TOKEN=xyz987"
    expected = "run-opt -e TEAGENT_ACCOUNT_TOKEN=<removed>"
    assert sanitizer.remove_app_hosting(config) == expected

def test_multiple_lines():
    sanitizer = ConfigSanitizer()
    config = """app-hosting run-opts appid thousandeyes
  run-opt --env TEAGENT_ACCOUNT_TOKEN=abcd1234
  run-opt -e TEAGENT_ACCOUNT_TOKEN=xyz987"""
    expected = """app-hosting run-opts appid thousandeyes
  run-opt --env TEAGENT_ACCOUNT_TOKEN=<removed>
  run-opt -e TEAGENT_ACCOUNT_TOKEN=<removed>"""
    assert sanitizer.remove_app_hosting(config) == expected


@pytest.mark.parametrize("input_line,expected_line", [
    ("run-opt --env TEAGENT_ACCOUNT_TOKEN=mySecret", "run-opt --env TEAGENT_ACCOUNT_TOKEN=<removed>"),
    ("run-opt -e TEAGENT_ACCOUNT_TOKEN=mySecret", "run-opt -e TEAGENT_ACCOUNT_TOKEN=<removed>")
])
def test_parametrized(input_line, expected_line):
    sanitizer = ConfigSanitizer()
    assert sanitizer.remove_app_hosting(input_line) == expected_line
