import requests
import pyperclip

# Input: Reddit comment link
COMMENT_URL = "https://www.reddit.com/r/science/comments/1nu94z4/comment/nh05i30/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button"

# Test with a link post (uncomment to test)
# COMMENT_URL = "https://www.reddit.com/r/technology/comments/1ftgvrz/comment/lppm3im/"


def get_comment_chain(url):
    """Scrape the comment chain from Reddit and return formatted text."""

    # Add ?context=10000 to get full parent chain
    base_url = url.split('?')[0]
    json_url = base_url + '.json?context=10000'

    # Set a user agent to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(json_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # Extract the comment thread
    # data[0] is the post, data[1] is the comments
    post_data = data[0]['data']['children'][0]['data']
    comments_data = data[1]['data']['children']

    # Build the conversation chain
    conversation = []

    # Add LLM instructions at the top
    instructions = """INSTRUCTIONS FOR LLM:

You are engaging in an online debate on Reddit. You will take a politically conservative stance on the issue being argued.

Your username is: Misc1

IMPORTANT RULES:
- Keep your response similar in length to the comment you're responding to (the last comment in the chain)
- NEVER use bulleted or numbered lists in the final comment
- NEVER use em dashes (—) in the final comment
- Write naturally and human-like to appear as an authentic Reddit comment
- Your goal is to craft a strong, well-reasoned rebuttal that effectively counters the last comment
- Always ensure your response is well-researched and factually grounded
- Format your final response inside a Python code block (```python) so it can be easily copied to Reddit

WORKFLOW:
1. First, perform a thorough strategic analysis of the opponent's last comment
2. Identify all possible counter-responses they might make to your reply
3. Assign probability weights to each potential counter-response
4. Show your strategic analysis before writing the comment
5. Craft your comment to preemptively address the most likely counter-responses (highest probability)
6. Present your final comment in a Python code block

Generate a reply to the last comment in the chain below.

---"""

    conversation.append(instructions)

    # Add the original post first
    post_author = post_data['author']
    post_title = post_data['title']
    post_body = post_data.get('selftext', '')
    post_url = post_data.get('url', '')

    # Build post content
    post_content = f"REDDIT POST:\n{post_author}: {post_title}"

    if post_body:
        post_content += f"\n\n{post_body}"

    # Add link if it exists and it's an external link (not reddit comments page)
    if post_url and '/comments/' not in post_url:
        post_content += f"\n\nLink: {post_url}"

    conversation.append(post_content)

    # Add comment section header
    conversation.append("COMMENT SECTION:")

    def extract_chain(comment_list):
        """Extract the linear comment chain (parent to child) - no children."""
        for item in comment_list:
            if item['kind'] == 't1':  # t1 is a comment
                comment = item['data']
                author = comment['author']
                body = comment['body']

                conversation.append(f"{author}: {body}")

                # Continue down the chain (only the direct parent chain, not siblings)
                if 'replies' in comment and comment['replies']:
                    extract_chain(comment['replies']['data']['children'])
                    break  # Only follow the first reply chain (the linked comment path)

    extract_chain(comments_data)

    return conversation


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
