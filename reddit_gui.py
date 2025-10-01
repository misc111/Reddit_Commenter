import tkinter as tk
import pyperclip
from scraper_utils import get_comment_chain


def handle_paste(event=None):
    """Handle CMD+V paste event and process the URL from clipboard."""
    try:
        # Get URL from clipboard
        url = root.clipboard_get().strip()
        print(f"\n=== PROCESSING PASTED URL ===")
        print(f"URL: {url}")

        if not url:
            status_label.config(text="Clipboard is empty", fg="orange", wraplength=350)
            return "break"  # Prevent default paste behavior

        if 'reddit.com' not in url:
            status_label.config(text="Not a Reddit link", fg="orange", wraplength=350)
            return "break"

        # Show processing message
        status_label.config(text="Processing...", fg="blue", wraplength=350)
        root.update()
        print("Fetching comment chain...")

        # Get dunk mode state
        dunk_mode = dunk_mode_var.get()
        print(f"Dunk Mode: {'ON' if dunk_mode else 'OFF'}")

        # Get the comment chain
        conversation = get_comment_chain(url, dunk_mode=dunk_mode)
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

        return "break"  # Prevent default paste behavior

    except tk.TclError:
        status_label.config(text="Clipboard is empty", fg="orange", wraplength=350)
        return "break"
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        status_label.config(text=f"✗ Error: {str(e)}", fg="red", wraplength=350)
        return "break"


# Create the main window
root = tk.Tk()
root.title("Reddit Comment Scraper")
root.geometry("400x230")
root.resizable(False, False)

# Create and pack widgets
title_label = tk.Label(root, text="Reddit Comment Chain Scraper", font=("Arial", 14, "bold"))
title_label.pack(pady=15)

instruction_label = tk.Label(root, text="Press ⌘+V to paste Reddit comment URL", font=("Arial", 11), fg="#555")
instruction_label.pack(pady=5)

# Dunk Mode checkbox
dunk_mode_var = tk.BooleanVar(value=False)
dunk_mode_checkbox = tk.Checkbutton(
    root,
    text="Dunk Mode 🏀",
    variable=dunk_mode_var,
    font=("Arial", 10)
)
dunk_mode_checkbox.pack(pady=10)

# Status label that shows results
status_label = tk.Label(root, text="Ready - paste URL with ⌘+V", font=("Arial", 10), fg="gray", wraplength=350, justify="left")
status_label.pack(pady=15, padx=20)

# Bind CMD+V (Mac) and CTRL+V (Windows/Linux) to handle paste
root.bind('<Command-v>', handle_paste)
root.bind('<Control-v>', handle_paste)

# Start the GUI only if run directly
if __name__ == "__main__":
    root.mainloop()
