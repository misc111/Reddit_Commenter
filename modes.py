"""Mode definitions and prompt configuration helpers.

Centralizing these values keeps the GUI, scraper, and prompt template in
lockstep while still allowing us to extend the set of modes without
hand-editing multiple files. Nothing in this module alters runtime
behaviour—it only formalizes constants that already existed elsewhere.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, Mapping


class Mode(str, Enum):
    """Supported conversation modes.

    The values intentionally stay identical to the strings we already pass
    across the application so existing functionality continues to work.
    """

    AGREE = "agree"
    FRIENDLY = "friendly"
    STANDARD = "standard"
    DUNK = "dunk"

    @classmethod
    def from_value(cls, value: str) -> "Mode":
        """Normalize a string into a ``Mode`` instance."""

        try:
            return cls(value)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Unsupported mode: {value}") from exc

    @property
    def ui_label(self) -> str:
        """Return the human-friendly label used in the GUI."""

        return MODE_DISPLAY_LABELS[self]


DEFAULT_MODE: Mode = Mode.STANDARD

# Order that communicates the "agreeability" scale left-to-right.
MODE_UI_ORDER: Iterable[Mode] = (
    Mode.AGREE,
    Mode.FRIENDLY,
    Mode.STANDARD,
    Mode.DUNK,
)

MODE_DISPLAY_LABELS: Mapping[Mode, str] = {
    Mode.AGREE: "Agree ✅",
    Mode.FRIENDLY: "Friendly 🤝",
    Mode.STANDARD: "Standard 💼",
    Mode.DUNK: "Dunk 🏀",
}


# Placeholders we expect to swap out inside ``llm_prompt.txt``.
PROMPT_PLACEHOLDERS = (
    "STANCE",
    "TONE",
    "MODE_SPECIFIC_GUIDANCE",
    "LENGTH_REQUIREMENT",
    "PHASE2_REQUIREMENTS",
    "PHASE3_REQUIREMENTS",
    "PHASE4_LENGTH_TARGET",
    "PHASE4_COUNTER_GUIDANCE",
)


BASE_PROMPT_CONFIG: Mapping[str, str] = {
    "STANCE": (
        "Take a politically conservative stance on the issue being argued. You're "
        "here to disagree and present a counter-perspective."
    ),
    "TONE": (
        "STANDARD MODE: Be direct, fact-based, and to the point - think Ben Shapiro "
        "style. Present your conservative perspective with clarity and confidence. "
        "You're not here to be friendly, but you're also not overtly aggressive. "
        "State facts, make logical arguments, and directly challenge flawed reasoning. "
        "Use a matter-of-fact tone that says 'here's why you're wrong' without being "
        "unnecessarily combative. Be assertive and unapologetic about your position, "
        "but let the facts do the heavy lifting rather than personal attacks."
    ),
    "MODE_SPECIFIC_GUIDANCE": "",
    "LENGTH_REQUIREMENT": (
        "LENGTH MATCHING IS MANDATORY: Your final comment MUST be approximately the "
        "same length as the comment you're responding to (the last comment in the "
        "chain). You may be 1-2 sentences longer, but NO MORE. This is about matching "
        "the effort level of the person you're responding to."
    ),
    "PHASE2_REQUIREMENTS": (
        "Show your strategic thinking:\n"
        "- Analyze the opponent's last comment in detail\n"
        "- Identify their main claims, assumptions, and logical structure\n"
        "- Assess the strength of their argument and potential weaknesses\n"
        "- Consider how your research findings (if applicable) or logical reasoning "
        "can effectively counter their points\n"
        "- EXPLICITLY WRITE OUT your strategic analysis before moving to the next phase"
    ),
    "PHASE3_REQUIREMENTS": (
        "Show your counter-response predictions:\n"
        "- Identify ALL possible counter-responses the opponent might make to your reply\n"
        "- Assign probability weights (%) to EACH potential counter-response\n"
        "- List them out explicitly (e.g., \"Response A: 40%, Response B: 30%, "
        "Response C: 20%, Response D: 10%\")\n"
        "- Explain which high-probability responses you will preemptively address and HOW\n"
        "- SHOW ALL OF THIS ANALYSIS in your response before moving to the next phase"
    ),
    "PHASE4_LENGTH_TARGET": (
        "Set your target length: approximately the same length, or at most 1-2 "
        "sentences longer"
    ),
    "PHASE4_COUNTER_GUIDANCE": (
        "- Explain how you'll preemptively address the most likely counter-responses "
        "in each draft"
    ),
}


MODE_PROMPT_OVERRIDES: Mapping[Mode, Mapping[str, str]] = {
    Mode.FRIENDLY: {
        "STANCE": (
            "Take the most objective, well-reasoned position on the topic, regardless "
            "of whether it strictly aligns with conservative ideology. Your goal is to "
            "find common ground and contribute meaningfully to the discussion."
        ),
        "TONE": (
            "FRIENDLY MODE: Use a warm, thoughtful, and genuinely respectful tone. You're "
            "here to share insights and engage in meaningful dialogue. Be personable and "
            "open-minded - like you're having a conversation with a friend over coffee. "
            "Focus on understanding their perspective while offering your own thoughtful "
            "take. Use phrases like 'That's an interesting point,' 'I can see where "
            "you're coming from,' 'Here's how I think about it,' or 'What if we "
            "considered...' Avoid any hint of confrontation or debate."
        ),
    },
    Mode.DUNK: {
        "STANCE": (
            "Take a politically conservative stance on the issue being argued. Your "
            "goal is to completely dismantle the opposing position."
        ),
        "TONE": (
            "DUNK MODE ACTIVATED: Be ruthless, cutting, and mercilessly critical. Call "
            "out weak reasoning, expose logical fallacies by name, and demolish their "
            "argument piece by piece. Use sharp, incisive language that leaves no room "
            "for their position. Be unapologetically aggressive while staying factually "
            "grounded. The goal is to completely dismantle their argument and make them "
            "regret engaging. This is a debate, and you're here to win decisively."
        ),
    },
    Mode.AGREE: {
        "STANCE": (
            "AGREE MODE: You are aligned with the final commenter. Reinforce their core "
            "points, add supporting context, and strengthen their position without "
            "undermining it."
        ),
        "TONE": (
            "AGREE MODE TONE: Be encouraging, confident, and collaborative. Sound like a "
            "thoughtful ally who appreciates the original point and is eager to build on "
            "it with useful detail or personal insight."
        ),
        "MODE_SPECIFIC_GUIDANCE": (
            "AGREE MODE DIRECTIVE: This is not a debate. Focus on amplifying and "
            "enhancing the final comment rather than arguing against anyone."
        ),
        "LENGTH_REQUIREMENT": (
            "LENGTH FLEXIBILITY: Aim to match the length of the comment you're supporting, "
            "but you may go up to roughly 150% of its length if needed to add meaningful "
            "reinforcement or context."
        ),
        "PHASE2_REQUIREMENTS": (
            "Agree mode is collaborative, so no strategic takedown is needed. Provide a "
            "brief note such as \"Strategic Analysis: N/A - Agree mode (reinforcing, "
            "not debating).\""
        ),
        "PHASE3_REQUIREMENTS": (
            "Agree mode does not require anticipating counter-responses. Provide a note "
            "such as \"Counter-Response Prediction: N/A - Agree mode.\""
        ),
        "PHASE4_LENGTH_TARGET": (
            "Set your target length to roughly match the original comment, with "
            "permission to go up to about 150% if that's helpful for reinforcement"
        ),
        "PHASE4_COUNTER_GUIDANCE": (
            "- Instead of counter-response planning, explain how each draft will reinforce "
            "and expand on the original comment while keeping the supportive tone "
            "consistent"
        ),
    },
}


def get_prompt_config(mode: Mode) -> Dict[str, str]:
    """Return the mapping of template placeholders for ``mode``."""

    config = dict(BASE_PROMPT_CONFIG)
    overrides = MODE_PROMPT_OVERRIDES.get(mode, {})
    config.update(overrides)

    missing_keys = {key for key in PROMPT_PLACEHOLDERS if key not in config}
    if missing_keys:  # pragma: no cover - defensive (should never trigger)
        raise KeyError(f"Prompt config missing keys: {sorted(missing_keys)}")

    return config
