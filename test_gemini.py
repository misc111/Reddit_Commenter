#!/usr/bin/env python3
"""Test script for the Gemini integration."""

import sys
import time
import subprocess
import pyperclip

print("=" * 60)
print("GEMINI INTEGRATION TEST")
print("=" * 60)

# Test 1: Create mock conversation data
print("\n[TEST 1] Creating mock conversation data...")
mock_conversation = [
    "You are engaging in an online debate on Reddit...",
    "REDDIT POST:\nTestUser: This is a test post about technology",
    "COMMENT SECTION:",
    "User1: I think this technology is amazing!",
    "User2: I disagree, here are my reasons..."
]
full_text = '\n\n'.join(mock_conversation)
print(f"✓ Mock conversation created ({len(full_text)} characters)")
print(f"  Preview: {full_text[:100]}...")

# Test 2: Copy to clipboard
print("\n[TEST 2] Copying conversation to clipboard...")
pyperclip.copy(full_text)
clipboard_content = pyperclip.paste()
if clipboard_content == full_text:
    print("✓ Successfully copied to clipboard")
    print(f"  Clipboard length: {len(clipboard_content)} characters")
else:
    print("✗ Clipboard content doesn't match!")
    sys.exit(1)

# Test 3: Check if Safari is running
print("\n[TEST 3] Checking Safari status...")
try:
    result = subprocess.run(
        ['osascript', '-e', 'tell application "System Events" to (name of processes) contains "Safari"'],
        capture_output=True,
        text=True,
        check=True
    )
    safari_running = result.stdout.strip() == "true"
    print(f"  Safari running: {safari_running}")
except Exception as e:
    print(f"✗ Error checking Safari status: {e}")
    safari_running = False

# Test 4: Execute AppleScript to open Gemini
print("\n[TEST 4] Executing AppleScript to open Safari and Gemini...")
print("  This will:")
print("  - Activate Safari")
print("  - Create new tab (or window if none exist)")
print("  - Navigate to gemini.google.com")
print("  - Wait 2 seconds")
print("  - Paste the conversation with CMD+V")
print()

applescript = '''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document
        log "Created new Safari window"
    else
        tell front window
            set current tab to (make new tab)
            log "Created new tab in existing window"
        end tell
    end if
    delay 0.5
    set URL of front document to "https://gemini.google.com"
    log "Navigated to Gemini"
    delay 2
end tell

tell application "System Events"
    tell process "Safari"
        keystroke "v" using command down
        log "Pasted content with CMD+V"
    end tell
end tell

return "Success"
'''

try:
    print("  Executing AppleScript...")
    result = subprocess.run(
        ['osascript', '-e', applescript],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )
    print(f"✓ AppleScript executed successfully")
    print(f"  Return value: {result.stdout.strip()}")
    if result.stderr:
        print(f"  AppleScript log: {result.stderr.strip()}")
except subprocess.TimeoutExpired:
    print("✗ AppleScript execution timed out (>10 seconds)")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"✗ AppleScript execution failed")
    print(f"  Return code: {e.returncode}")
    print(f"  stdout: {e.stdout}")
    print(f"  stderr: {e.stderr}")

    if "not allowed to send keystrokes" in e.stderr or "1002" in e.stderr:
        print("\n" + "!" * 60)
        print("ACCESSIBILITY PERMISSION REQUIRED")
        print("!" * 60)
        print("\nThe script needs permission to control your computer.")
        print("\nTo fix this:")
        print("1. Open System Preferences/Settings")
        print("2. Go to Privacy & Security > Accessibility")
        print("3. Add 'Terminal' or your terminal app to the list")
        print("4. Grant it permission")
        print("5. Restart this test")
        print("\nAlternatively, if running from an IDE:")
        print("- Add your IDE (VS Code, PyCharm, etc.) to Accessibility")
        print("!" * 60)
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify Safari window
print("\n[TEST 5] Verifying Safari state...")
try:
    check_script = '''
    tell application "Safari"
        set windowCount to count of windows
        if windowCount > 0 then
            set currentURL to URL of front document
            return "Windows: " & windowCount & ", URL: " & currentURL
        else
            return "No windows open"
        end if
    end tell
    '''
    result = subprocess.run(
        ['osascript', '-e', check_script],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"✓ Safari verification: {result.stdout.strip()}")
except Exception as e:
    print(f"✗ Could not verify Safari state: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nPlease verify manually:")
print("1. Safari opened/created a new tab")
print("2. The URL is gemini.google.com")
print("3. The conversation was pasted in the chat box")
print("\nIf all three conditions are met, the test passed!")
print("=" * 60)
