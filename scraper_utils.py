import requests
import os


def load_llm_prompt():
    """Load the LLM prompt from the text file."""
    prompt_path = os.path.join(os.path.dirname(__file__), 'llm_prompt.txt')
    with open(prompt_path, 'r') as f:
        return f.read()


def get_comment_chain(url):
    """Scrape the comment chain from Reddit and return formatted text."""

    # Extract comment ID from URL
    # URL format: .../comment/COMMENT_ID/...
    target_comment_id = None
    if '/comment/' in url:
        parts = url.split('/comment/')
        if len(parts) > 1:
            target_comment_id = parts[1].split('/')[0].split('?')[0]

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
    instructions = load_llm_prompt()
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

    # Flag to stop extraction once we hit the target comment
    found_target = [False]

    def extract_chain(comment_list, depth=0):
        """Extract parent chain up to and including the linked comment."""
        if depth > 50 or found_target[0]:  # Stop if we found target or hit depth limit
            return

        for item in comment_list:
            if item['kind'] != 't1':  # Skip if not a comment
                continue

            comment = item['data']
            comment_id = comment['id']
            author = comment['author']
            body = comment['body']

            # Add this comment
            conversation.append(f"{author}: {body}")

            # Check if this is the target comment
            if target_comment_id and comment_id == target_comment_id:
                found_target[0] = True
                return

            # Follow replies to continue the chain
            replies = comment.get('replies')
            if replies and isinstance(replies, dict) and 'data' in replies:
                children = replies['data'].get('children', [])
                if children:
                    extract_chain(children, depth + 1)

            # Only process the first comment in each level (the direct chain)
            break

    extract_chain(comments_data)

    return conversation
