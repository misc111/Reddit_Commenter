#!/usr/bin/env python3
"""Test script that simulates clicking the button and auto-closes after success."""

import sys
import os

# First test the core function
print("=== Testing core function first ===")
from reddit_gui import get_comment_chain

url = "https://www.reddit.com/r/science/comments/1nu94z4/comment/nh05i30/"
print(f"URL: {url}")

try:
    conversation = get_comment_chain(url)
    print(f"✓ Core function works: {len(conversation)} items extracted\n")
except Exception as e:
    print(f"✗ Core function failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Now test the GUI
import tkinter as tk
import threading
import time

import reddit_gui

test_complete = False

def auto_click():
    """Click button after short delay."""
    time.sleep(0.3)
    print("\n=== Testing GUI ===")
    # Insert test URL
    test_url = "https://www.reddit.com/r/science/comments/1nu94z4/comment/nh05i30/"
    reddit_gui.entry.insert(0, test_url)
    print(f"Entry value: {reddit_gui.entry.get()}")
    print("Clicking button...")
    reddit_gui.button.invoke()

def check_result():
    """Check if test completed."""
    time.sleep(5)
    global test_complete
    test_complete = True
    print(f"\nFinal status: {reddit_gui.status_label.cget('text')}")
    if "Successfully" in reddit_gui.status_label.cget('text'):
        print("\n=== TEST PASSED ===")
    else:
        print("\n=== TEST FAILED ===")
    reddit_gui.root.quit()

threading.Thread(target=auto_click, daemon=True).start()
threading.Thread(target=check_result, daemon=True).start()

reddit_gui.root.mainloop()
sys.exit(0)
