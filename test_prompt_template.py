import re

import pytest

from modes import Mode
from scraper_utils import load_llm_prompt


@pytest.mark.parametrize("mode", [mode.value for mode in Mode])
def test_prompt_has_no_placeholders_remaining(mode: str) -> None:
    prompt = load_llm_prompt(mode=mode)
    leftovers = re.findall(r"{{\s*([\w_]+)\s*}}", prompt)
    assert not leftovers, f"Unresolved placeholders for mode '{mode}': {leftovers}"
