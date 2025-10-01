import pyperclip
from scraper_utils import get_comment_chain

# Input: Reddit comment link
COMMENT_URL = "https://www.reddit.com/r/science/comments/1nu94z4/comment/ngzdh3r/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button"

# Test with a link post (uncomment to test)
# COMMENT_URL = "https://www.reddit.com/r/technology/comments/1ftgvrz/comment/lppm3im/"


if __name__ == "__main__":
    try:
        print("Scraping Reddit comment chain...\n")
        conversation = get_comment_chain(COMMENT_URL)

        # Print truncated test output
        print("=== CONVERSATION PREVIEW ===\n")
        for i, comment in enumerate(conversation[:10]):  # Show first 10 comments
            # Truncate long comments for display, but show more for the post
            if i == 0:  # First item is the post, show more to include link
                truncated = comment if len(comment) <= 500 else comment[:497] + "..."
            else:
                truncated = comment if len(comment) <= 100 else comment[:97] + "..."
            print(truncated)
            print()  # Add blank line between items

        if len(conversation) > 10:
            print(f"\n... ({len(conversation) - 10} more comments)")

        print(f"\n=== TOTAL: {len(conversation)} comments ===\n")

        # Copy full conversation to clipboard
        full_text = '\n\n'.join(conversation)
        pyperclip.copy(full_text)

        print("✓ Full conversation copied to clipboard!")

    except Exception as e:
        print(f"Error: {e}")
