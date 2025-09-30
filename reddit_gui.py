import tkinter as tk
from tkinter import messagebox
import pyperclip
import requests


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

NOTE: Sometimes Misc1 (you) may have already commented in the chain, and other times you are just entering the conversation. Either way, your task is to generate a rebuttal to the LAST comment in the chain.

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

    def extract_chain(comment_list, depth=0):
        """Extract the linear comment chain (parent to linked comment only) - no children."""
        if depth > 50:  # Safety check to prevent infinite recursion
            return

        for item in comment_list:
            if item['kind'] != 't1':  # Skip if not a comment
                continue

            comment = item['data']
            author = comment['author']
            body = comment['body']

            # Add this comment
            conversation.append(f"{author}: {body}")

            # Check if there are replies to continue the chain
            replies = comment.get('replies')
            if replies and isinstance(replies, dict) and 'data' in replies:
                children = replies['data'].get('children', [])
                if children:
                    extract_chain(children, depth + 1)

            # Only process the first comment in each level (the direct chain)
            break

    extract_chain(comments_data)

    return conversation


def process_link():
    url = entry.get().strip()
    print(f"\n=== PROCESSING LINK ===")
    print(f"URL: {url}")

    if not url:
        messagebox.showwarning("Empty Input", "Please paste a Reddit comment link")
        return

    if 'reddit.com' not in url:
        messagebox.showerror("Invalid URL", "Please enter a valid Reddit comment link")
        return

    try:
        # Show processing message
        status_label.config(text="Processing...", fg="blue")
        root.update()
        print("Fetching comment chain...")

        # Get the comment chain
        conversation = get_comment_chain(url)
        full_text = '\n\n'.join(conversation)

        # Print preview
        print(f"\n=== CONVERSATION PREVIEW ===")
        for i, item in enumerate(conversation[:5]):
            if i == 0:
                print("\n[INSTRUCTIONS]")
                print(item[:150] + "...")
            elif i == 1:
                print("\n[POST]")
                print(item[:150] + "...")
            elif i == 2:
                print("\n[COMMENTS]")
            else:
                print(item[:100] + "..." if len(item) > 100 else item)

        if len(conversation) > 5:
            print(f"\n... and {len(conversation) - 5} more items")

        print(f"\n=== TOTAL: {len(conversation)} items ===")

        # Copy to clipboard
        pyperclip.copy(full_text)
        print("✓ Copied to clipboard!")

        # Show success message
        status_label.config(text="✓ Successfully copied comment chain!", fg="green")
        entry.delete(0, tk.END)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        status_label.config(text="Error processing link", fg="red")
        messagebox.showerror("Error", f"Failed to process link:\n{str(e)}")


# Create the main window
root = tk.Tk()
root.title("Reddit Comment Scraper")
root.geometry("450x180")
root.resizable(False, False)

# Create and pack widgets
title_label = tk.Label(root, text="Reddit Comment Chain Scraper", font=("Arial", 14, "bold"))
title_label.pack(pady=15)

instruction_label = tk.Label(root, text="Paste Reddit comment link below:", font=("Arial", 10))
instruction_label.pack(pady=5)

entry = tk.Entry(root, width=50, font=("Arial", 10))
entry.pack(pady=5)
entry.focus()

# Bind Enter key to process
entry.bind('<Return>', lambda e: process_link())

button = tk.Button(root, text="Copy Comment Chain", command=process_link, font=("Arial", 11, "bold"), bg="#FF4500", fg="white", padx=20, pady=8)
button.pack(pady=10)

status_label = tk.Label(root, text="", font=("Arial", 9))
status_label.pack(pady=5)

# Start the GUI only if run directly
if __name__ == "__main__":
    root.mainloop()
