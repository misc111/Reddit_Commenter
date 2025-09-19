# Reddit Commenter Bot

The project monitors a subreddit for comments containing configured keywords, proposes an AI-generated conservative reply, and lets you manually approve posting.

## Prerequisites
- Python 3.9+
- A `config.ini` file containing your Reddit credentials and settings (same format as before).
- Python packages: `praw` and `requests` (install with `pip install praw requests`).

## Environment Variables
1. Copy `.env.example` to `.env` and set your values:
   ```env
   OPENAI_API_KEY=sk-your-openai-key
   OPENAI_MODEL=gpt-4o-mini    # optional override
   OPENAI_TEMPERATURE=0.6      # optional override
   ```
2. Without `OPENAI_API_KEY`, the bot falls back to a canned reply.

## Running the CLI workflow
```bash
python main.py
```
The CLI shows each candidate reply in the terminal and asks whether to post it.

## Running the desktop UI
```bash
python ui.py
```
The Tkinter UI streams matching comments, shows the full thread context, and lets you approve, skip, or refresh items in the queue. Close the window to stop the background stream.

## Notes
- Replies are never posted automatically; both the CLI and UI require your confirmation.
- Throttling still applies—after each approved reply the bot pauses briefly to respect Reddit rate limits.
- Logged output is written to stdout; adjust the logging configuration in `bot_core.py` if you need different behaviour.
