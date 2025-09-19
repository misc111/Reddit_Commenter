"""CLI entry point for the Reddit commenter bot."""
import logging

from bot_core import PendingReply, RedditBot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def prompt_user(pending: PendingReply) -> bool:
    """Display the generated reply and ask the user whether to post it."""
    print("--- NEW REPLY ---")
    print(f"Matched keyword: {pending.matched_keyword}")
    print(f"Original Comment: {pending.comment.body}\n")
    print(f"Generated Reply: {pending.suggested_reply}\n")
    approval = input("Post this reply? (y/n): ")
    return approval.lower() == "y"


def main() -> None:
    """Run the interactive CLI loop for approving replies."""
    try:
        bot = RedditBot()
    except ValueError as config_error:
        logging.error("%s", config_error)
        return
    except Exception:
        logging.exception("Unexpected error while initialising the bot")
        return

    try:
        for pending in bot.iter_pending_replies():
            try:
                if prompt_user(pending):
                    bot.post_reply(pending)
                else:
                    logging.info(
                        "User declined to post reply to comment %s", pending.comment.id
                    )
            except KeyboardInterrupt:
                raise
            except Exception:
                logging.exception(
                    "Error while handling comment %s", pending.comment.id
                )
    except KeyboardInterrupt:
        logging.info("Stopping bot at user request...")
        bot.stop()
    except Exception:
        logging.exception("Fatal error while streaming comments")


if __name__ == "__main__":
    main()
