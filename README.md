# Reddit Commenter

Utility for grabbing a Reddit comment chain and handing it to a local LLM
workflow. The GUI (`reddit_gui.py`) provides a one-click pipeline: paste a
comment URL, copy the formatted chain, and optionally open it directly in
Gemini.

## Persona & Prompt Template

The LLM prompt lives in `llm_prompt.txt`. It contains placeholder tokens that
are replaced at runtime. These placeholders are declared centrally in
`modes.py`; if you introduce a new placeholder, add it to
`modes.PROMPT_PLACEHOLDERS` so missing replacements surface immediately.

Misc1—the persona used across modes—is detailed inside the prompt file and is
meant to be treated as internal guidance. Only mention the background if the
conversation makes it relevant (for example, responding to accusations about
ethnicity).

## Modes

The available modes are defined once in `modes.py` and consumed by both the
GUI and the prompt loader. To add a mode, supply a prompt override in
`MODE_PROMPT_OVERRIDES` and update `MODE_DISPLAY_LABELS` for the GUI label. The
`MODE_UI_ORDER` tuple controls left-to-right ordering in the GUI so more modes
can be introduced without touching the interface code.

| Mode      | Summary                                                                         |
|-----------|----------------------------------------------------------------------------------|
| Agree     | Reinforce and expand on the last commenter’s point. Skips adversarial workflow. |
| Friendly  | Seek common ground and respond in a warm, thoughtful tone.                       |
| Standard  | Classic counter-perspective: direct, factual, and unapologetic.                 |
| Dunk      | Aggressive rebuttal that dismantles the opposing comment.                        |

## Testing

`pytest` discovers a clipboard-driven integration harness (`test_gemini.py`).
It expects access to the system clipboard, so run it on a host where
`pyperclip` can interact with the native clipboard. Template validation lives
in `test_prompt_template.py` and offers quick verification that all modes still
produce a fully substituted prompt.
