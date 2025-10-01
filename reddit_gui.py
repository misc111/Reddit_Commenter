import tkinter as tk
import pyperclip
from scraper_utils import get_comment_chain


def process_clipboard():
    """Automatically process clipboard content when window receives focus."""
    try:
        # Get clipboard content
        url = root.clipboard_get().strip()
        print(f"\n=== PROCESSING CLIPBOARD ===")
        print(f"URL: {url}")

        if not url:
            status_label.config(text="Clipboard is empty", fg="orange", wraplength=350)
            return

        if 'reddit.com' not in url:
            status_label.config(text="Clipboard doesn't contain a Reddit link", fg="orange", wraplength=350)
            return

        # Show processing message
        status_label.config(text="Processing...", fg="blue", wraplength=350)
        root.update()
        print("Fetching comment chain...")

        # Get the comment chain
        conversation = get_comment_chain(url)
        full_text = '\n\n'.join(conversation)

        # Print preview
        print(f"\n=== CONVERSATION PREVIEW ===")
        comments = conversation[3:]  # Skip instructions, post, and "COMMENT SECTION:" header
        print(f"Post + {len(comments)} comments in chain")
        for i, comment in enumerate(comments):
            preview = comment[:80] + "..." if len(comment) > 80 else comment
            print(f"{i+1}. {preview}")

        print(f"\n=== TOTAL: {len(conversation)} items ===")

        # Copy full conversation to clipboard
        pyperclip.copy(full_text)
        print("✓ Copied to clipboard!")

        # Get last comment for display
        last_comment = comments[-1] if comments else "No comments found"

        # Truncate last comment for display
        if len(last_comment) > 150:
            display_text = last_comment[:147] + "..."
        else:
            display_text = last_comment

        # Show success message with last comment preview
        success_msg = f"✓ Success! Last comment:\n\n{display_text}"
        status_label.config(text=success_msg, fg="green", wraplength=350)

    except tk.TclError:
        status_label.config(text="Clipboard is empty", fg="orange", wraplength=350)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        status_label.config(text=f"✗ Error: {str(e)}", fg="red", wraplength=350)


# Create the main window
root = tk.Tk()
root.title("Reddit Comment Scraper")
root.geometry("400x200")
root.resizable(False, False)

# Create and pack widgets
title_label = tk.Label(root, text="Reddit Comment Chain Scraper", font=("Arial", 14, "bold"))
title_label.pack(pady=15)

instruction_label = tk.Label(root, text="Copy a Reddit comment link, then click here", font=("Arial", 10))
instruction_label.pack(pady=5)

# Status label that shows results
status_label = tk.Label(root, text="Ready to process clipboard", font=("Arial", 10), fg="gray", wraplength=350, justify="left")
status_label.pack(pady=15, padx=20)

# Bind window focus to auto-process
root.bind('<FocusIn>', lambda e: process_clipboard())

# Start the GUI only if run directly
if __name__ == "__main__":
    root.mainloop()
