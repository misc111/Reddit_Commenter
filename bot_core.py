"""Core logic for the Reddit commenter bot with OpenAI integration."""
from __future__ import annotations

import configparser
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

import praw
import requests
from praw.models import Comment


def load_env(dotenv_path: str = ".env") -> None:
    """Populate environment variables from a .env file if present."""
    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except OSError as env_error:
        logging.warning("Failed to read .env file at %s: %s", dotenv_path, env_error)


# Ensure any environment configuration is loaded before reading settings.
load_env()


CONFIG = configparser.ConfigParser()
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
if not CONFIG.read(CONFIG_PATH):
    logging.error("Unable to read configuration file at %s", CONFIG_PATH)
    raise SystemExit(1)

SETTINGS = CONFIG["settings"]
TARGET_SUBREDDIT = SETTINGS.get("target_subreddit", "").strip()
KEYWORDS: Iterable[str] = [
    keyword.strip().lower()
    for keyword in SETTINGS.get("keywords", "").split(",")
    if keyword.strip()
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.6"))

FALLBACK_REPLY = (
    "From a conservative viewpoint, the core of this issue seems to be about personal "
    "responsibility rather than a need for more regulation. Individuals should have "
    "the freedom to make their own choices, and the market will often provide a better "
    "solution than a government program."
)


@dataclass
class PendingReply:
    """Encapsulates a potential reply generated for a matched comment."""

    comment: Comment
    matched_keyword: str
    thread_context: str
    suggested_reply: str


def get_thread_context(comment: Comment) -> str:
    """Build a textual summary of the submission and parent comments leading to the trigger."""
    submission = comment.submission
    context_parts = [
        f"Submission Title: {submission.title}",
        f"Submission Body: {submission.selftext or '[No submission body]'}",
    ]

    parent_comments = []
    current = comment
    while True:
        parent = current.parent()
        if isinstance(parent, Comment):
            parent_comments.append(parent)
            current = parent
        else:
            break
    parent_comments.reverse()

    for index, parent_comment in enumerate(parent_comments, start=1):
        author_name = parent_comment.author.name if parent_comment.author else "[deleted]"
        context_parts.append(
            f"Parent Comment {index} by {author_name}:\n{parent_comment.body}"
        )

    trigger_author = comment.author.name if comment.author else "[deleted]"
    context_parts.append(f"Trigger Comment by {trigger_author}:\n{comment.body}")
    return "\n\n".join(context_parts)


def _call_openai_api(prompt: str) -> Optional[str]:
    """Send the prompt to OpenAI's chat completions endpoint and return the reply text."""
    if not OPENAI_API_KEY:
        logging.warning("OPENAI_API_KEY is not set; reverting to fallback reply text.")
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a commentator with a conservative perspective."
                    " Provide concise, relevant responses without being inflammatory."
                    " Focus on personal responsibility, limited government, and free markets."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": OPENAI_TEMPERATURE,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            logging.error("OpenAI response missing choices: %s", data)
            return None
        message = choices[0].get("message", {})
        content = message.get("content")
        if not content:
            logging.error("OpenAI response missing content: %s", data)
            return None
        return content.strip()
    except requests.RequestException as request_error:
        logging.exception("OpenAI API request failed: %s", request_error)
        return None


def generate_ai_comment(thread_context: str) -> str:
    """Generate an AI-powered comment or fall back to a static response."""
    prompt = (
        "Analyze the following Reddit thread and provide a concise conservative response.\n" 
        "Thread context:\n{thread_context}"
    ).format(thread_context=thread_context)

    ai_reply = _call_openai_api(prompt)
    if ai_reply:
        return ai_reply
    return FALLBACK_REPLY


class RedditBot:
    """Encapsulates Reddit authentication, streaming, and reply management."""

    def __init__(self) -> None:
        if not TARGET_SUBREDDIT:
            raise ValueError("Target subreddit is not defined in config.ini")
        if not KEYWORDS:
            raise ValueError("No keywords specified in config.ini")

        self.replied_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "replied_comments.txt"
        )
        self.replied_ids_cache = set()  # Cache known IDs to minimize disk reads.
        self.reddit: Optional[praw.Reddit] = None
        self.current_username: Optional[str] = None
        self._stop_event = threading.Event()

    def authenticate(self) -> praw.Reddit:
        """Authenticate with Reddit using credentials from the configuration file."""
        reddit = praw.Reddit(
            client_id=CONFIG["reddit"].get("client_id"),
            client_secret=CONFIG["reddit"].get("client_secret"),
            user_agent=CONFIG["reddit"].get("user_agent"),
            username=CONFIG["reddit"].get("username"),
            password=CONFIG["reddit"].get("password"),
        )
        reddit.user.me()  # Trigger API call to validate credentials.
        self.reddit = reddit
        try:
            current_user = reddit.user.me()
            self.current_username = current_user.name if current_user else None
        except Exception:
            logging.warning(
                "Unable to determine authenticated username; self-reply checks may be unreliable."
            )
        logging.info("Authenticated as %s", self.current_username)
        return reddit

    def stop(self) -> None:
        """Signal that streaming should halt at the next opportunity."""
        self._stop_event.set()

    def _ensure_authenticated(self) -> None:
        if self.reddit is None:
            self.authenticate()

    def _load_replied_ids(self) -> None:
        if self.replied_ids_cache:
            return
        try:
            with open(self.replied_file, "r", encoding="utf-8") as file:
                self.replied_ids_cache = {line.strip() for line in file if line.strip()}
        except FileNotFoundError:
            self.replied_ids_cache = set()

    def has_already_replied(self, comment_id: str) -> bool:
        self._load_replied_ids()
        return comment_id in self.replied_ids_cache

    def record_reply(self, comment_id: str) -> None:
        self.replied_ids_cache.add(comment_id)
        with open(self.replied_file, "a", encoding="utf-8") as file:
            file.write(f"{comment_id}\n")

    def iter_pending_replies(self) -> Iterator[PendingReply]:
        """Yield PendingReply instances for comments that match the configured keywords."""
        self._ensure_authenticated()
        assert self.reddit is not None
        subreddit = self.reddit.subreddit(TARGET_SUBREDDIT)
        logging.info("Monitoring new comments in r/%s", TARGET_SUBREDDIT)

        while not self._stop_event.is_set():
            try:
                for comment in subreddit.stream.comments(skip_existing=True):
                    if self._stop_event.is_set():
                        return
                    try:
                        pending = self._evaluate_comment(comment)
                        if pending:
                            yield pending
                    except Exception as comment_error:
                        logging.exception(
                            "Error processing comment %s: %s",
                            getattr(comment, "id", "unknown"),
                            comment_error,
                        )
            except Exception as stream_error:
                logging.exception("Error in comment stream: %s", stream_error)
                time.sleep(10)

    def _evaluate_comment(self, comment: Comment) -> Optional[PendingReply]:
        if not isinstance(comment, Comment):
            return None

        author_name = comment.author.name if comment.author else None
        if self.current_username and author_name == self.current_username:
            return None

        if self.has_already_replied(comment.id):
            return None

        body_lower = comment.body.lower()
        matched_keyword = next((kw for kw in KEYWORDS if kw in body_lower), None)
        if not matched_keyword:
            return None

        logging.info("Comment %s matched keyword '%s'", comment.id, matched_keyword)

        thread_context = get_thread_context(comment)
        reply_text = generate_ai_comment(thread_context)

        return PendingReply(
            comment=comment,
            matched_keyword=matched_keyword,
            thread_context=thread_context,
            suggested_reply=reply_text,
        )

    def post_reply(
        self,
        pending: PendingReply,
        reply_text: Optional[str] = None,
        *,
        sleep_after: bool = True,
    ) -> None:
        """Post the reply to Reddit and record the comment ID."""
        reply_body = reply_text or pending.suggested_reply
        pending.comment.reply(body=reply_body)
        self.record_reply(pending.comment.id)
        logging.info("Posted reply to comment %s", pending.comment.id)
        if sleep_after:
            time.sleep(60)


__all__ = [
    "KEYWORDS",
    "PendingReply",
    "RedditBot",
    "TARGET_SUBREDDIT",
    "generate_ai_comment",
]
