import tkinter as tk
import pyperclip
import subprocess
from scraper_utils import get_comment_chain


# Store the processed conversation globally
last_conversation = None


def handle_paste(event=None):
    """Handle CMD+V paste event and process the URL from clipboard."""
    global last_conversation
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
        last_conversation = conversation  # Store for later use
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

        # Enable the Gemini button with vibrant Gemini blue
        gemini_button.config(state="normal", bg="#1a73e8", fg="white")

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


def open_gemini():
    """Open Safari, navigate to Gemini, and paste the conversation."""
    global last_conversation

    if not last_conversation:
        status_label.config(text="No conversation to send to Gemini", fg="orange", wraplength=350)
        return

    try:
        # Copy conversation to clipboard for pasting
        full_text = '\n\n'.join(last_conversation)
        pyperclip.copy(full_text)

        # AppleScript to open Safari, create new tab, navigate to Gemini, and paste
        applescript = '''
        tell application "Safari"
            activate
            if (count of windows) = 0 then
                make new document
            else
                tell front window
                    set current tab to (make new tab)
                end tell
            end if
            delay 0.5
            set URL of front document to "https://gemini.google.com"
            delay 2
        end tell

        tell application "System Events"
            tell process "Safari"
                keystroke "v" using command down
            end tell
        end tell
        '''

        subprocess.run(['osascript', '-e', applescript], check=True)
        print("✓ Opened Gemini in Safari and pasted conversation")
        status_label.config(text="✓ Opened Gemini in Safari", fg="blue", wraplength=350)

    except Exception as e:
        print(f"ERROR opening Gemini: {e}")
        import traceback
        traceback.print_exc()
        status_label.config(text=f"✗ Error opening Gemini: {str(e)}", fg="red", wraplength=350)


# Create the main window
root = tk.Tk()
root.title("Reddit Comment Scraper")
root.geometry("400x280")
root.resizable(False, False)
root.config(bg="#1e1e1e")

# Create and pack widgets
title_label = tk.Label(
    root,
    text="Reddit Comment Chain Scraper",
    font=("Arial", 14, "bold"),
    bg="#1e1e1e",
    fg="#ffffff"
)
title_label.pack(pady=(20, 10))

instruction_label = tk.Label(
    root,
    text="Press ⌘+V to paste Reddit comment URL",
    font=("Arial", 11),
    bg="#1e1e1e",
    fg="#cccccc"
)
instruction_label.pack(pady=5)

# Dunk Mode checkbox
dunk_mode_var = tk.BooleanVar(value=False)
dunk_mode_checkbox = tk.Checkbutton(
    root,
    text="Dunk Mode 🏀",
    variable=dunk_mode_var,
    font=("Arial", 10),
    bg="#1e1e1e",
    fg="#ffffff",
    selectcolor="#2d2d2d",
    activebackground="#1e1e1e",
    activeforeground="#ffffff"
)
dunk_mode_checkbox.pack(pady=10)

# Open in Gemini button (disabled by default)
gemini_button = tk.Button(
    root,
    text="Open in Gemini 💎",
    command=open_gemini,
    font=("Arial", 11, "bold"),
    bg="#666666",
    fg="#999999",
    activebackground="#1557b0",
    activeforeground="white",
    relief="flat",
    borderwidth=0,
    padx=20,
    pady=8,
    cursor="hand2",
    state="disabled"
)
gemini_button.pack(pady=15)

# Status label that shows results
status_label = tk.Label(
    root,
    text="Ready - paste URL with ⌘+V",
    font=("Arial", 12),
    bg="#1e1e1e",
    fg="#888888",
    wraplength=350,
    justify="left"
)
status_label.pack(pady=(15, 20), padx=20)

# Bind CMD+V (Mac) and CTRL+V (Windows/Linux) to handle paste
root.bind('<Command-v>', handle_paste)
root.bind('<Control-v>', handle_paste)

# Start the GUI only if run directly
if __name__ == "__main__":
    root.mainloop()
