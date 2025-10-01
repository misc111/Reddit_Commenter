import tkinter as tk
from tkinter import ttk
import pyperclip
from scraper_utils import get_comment_chain, load_llm_prompt


def copy_chain_up_to(index):
    """Copy the conversation chain up to the selected comment index to clipboard."""
    # Build the chain: instructions + post + "COMMENT SECTION:" + comments up to index
    chain = conversation[:index + 1]
    full_text = '\n\n'.join(chain)
    pyperclip.copy(full_text)
    status_label.config(text=f"✓ Copied chain up to comment #{index - 2}", fg="green")
    print(f"\n✓ Copied chain up to index {index} (comment #{index - 2})")


def process_clipboard():
    """Automatically process clipboard content when window receives focus."""
    try:
        # Get clipboard content
        url = root.clipboard_get().strip()
        print(f"\n=== PROCESSING CLIPBOARD ===")
        print(f"URL: {url}")

        if not url:
            status_label.config(text="Clipboard is empty", fg="orange")
            return

        if 'reddit.com' not in url:
            status_label.config(text="Clipboard doesn't contain a Reddit link", fg="orange")
            return

        # Show processing message
        status_label.config(text="Processing...", fg="blue")
        root.update()

        # Get the comment chain
        global conversation
        conversation = get_comment_chain(url)

        # Clear previous comment buttons
        for widget in comment_frame.winfo_children():
            widget.destroy()

        # Display comments as clickable bubbles
        # conversation structure: [instructions, post, "COMMENT SECTION:", comment1, comment2, ...]
        comments = conversation[3:]  # Skip instructions, post, and "COMMENT SECTION:" header

        if not comments:
            status_label.config(text="No comments found", fg="orange")
            return

        status_label.config(text=f"Click a comment to set it as the target ({len(comments)} found)", fg="blue")

        for i, comment in enumerate(comments):
            # Extract author and preview
            if ':' in comment:
                author, body = comment.split(':', 1)
                preview = body.strip()[:80] + "..." if len(body.strip()) > 80 else body.strip()
            else:
                author = "Unknown"
                preview = comment[:80] + "..." if len(comment) > 80 else comment

            # Create button for each comment
            btn = tk.Button(
                comment_frame,
                text=f"{author}: {preview}",
                wraplength=500,
                justify="left",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=8,
                bg="white",
                activebackground="#e0e0e0",
                command=lambda idx=i+3: copy_chain_up_to(idx)  # idx offset by 3 for instructions, post, header
            )
            btn.pack(fill="x", padx=10, pady=5)

    except tk.TclError:
        status_label.config(text="Clipboard is empty", fg="orange")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        status_label.config(text=f"✗ Error: {str(e)}", fg="red")


# Create the main window
root = tk.Tk()
root.title("Reddit Comment Scraper")
root.geometry("600x500")
root.resizable(True, True)

# Global variable to store conversation
conversation = []

# Create and pack widgets
title_label = tk.Label(root, text="Reddit Comment Chain Scraper", font=("Arial", 14, "bold"))
title_label.pack(pady=10)

instruction_label = tk.Label(root, text="Copy a Reddit comment link, then click here", font=("Arial", 10))
instruction_label.pack(pady=5)

# Status label
status_label = tk.Label(root, text="Ready to process clipboard", font=("Arial", 10), fg="gray")
status_label.pack(pady=5)

# Scrollable frame for comments
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
comment_frame = tk.Frame(canvas)

comment_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=comment_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
scrollbar.pack(side="right", fill="y")

# Bind window focus to auto-process
root.bind('<FocusIn>', lambda e: process_clipboard())

# Start the GUI only if run directly
if __name__ == "__main__":
    root.mainloop()
