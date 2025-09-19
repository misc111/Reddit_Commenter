"""Tkinter-based UI for interacting with the Reddit commenter bot."""
import logging
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Union

from bot_core import PendingReply, RedditBot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class BotUI:
    """Simple desktop UI that surfaces pending replies for manual approval."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        try:
            self.bot = RedditBot()
        except ValueError as config_error:
            messagebox.showerror("Configuration Error", str(config_error))
            self.root.destroy()
            raise SystemExit(1) from config_error
        except Exception as init_error:
            logging.exception("Failed to initialise the Reddit bot")
            messagebox.showerror("Initialisation Error", str(init_error))
            self.root.destroy()
            raise SystemExit(1) from init_error
        self.root.title("Reddit Commenter Bot")
        self.root.geometry("900x700")

        self.status_var = tk.StringVar(value="Waiting for new matches...")

        status_label = tk.Label(
            self.root, textvariable=self.status_var, anchor="w", fg="#1d4ed8"
        )
        status_label.pack(fill="x", padx=12, pady=(12, 6))

        self.comment_text = self._build_text_area("Comment")
        self.reply_text = self._build_text_area("Suggested Reply")
        self.context_text = self._build_text_area("Thread Context")

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=12, pady=(6, 12))

        self.approve_button = tk.Button(
            button_frame,
            text="Approve & Post",
            command=self.on_approve,
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            padx=12,
            pady=6,
        )
        self.approve_button.pack(side="left", padx=(0, 8))

        self.skip_button = tk.Button(
            button_frame,
            text="Skip",
            command=self.on_skip,
            padx=12,
            pady=6,
        )
        self.skip_button.pack(side="left", padx=(0, 8))

        self.refresh_button = tk.Button(
            button_frame,
            text="Refresh",
            command=self.on_refresh,
            padx=12,
            pady=6,
        )
        self.refresh_button.pack(side="left")

        self.pending_queue: "queue.Queue[Union[PendingReply, tuple]]" = queue.Queue()
        self.pending_buffer: List[PendingReply] = []
        self.current_pending: Optional[PendingReply] = None

        self._stream_thread = threading.Thread(
            target=self._stream_worker, name="RedditStreamThread", daemon=True
        )
        self._posting_lock = threading.Lock()
        self._stream_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._clear_display()
        self.root.after(500, self._poll_queue)

    def _build_text_area(self, title: str) -> ScrolledText:
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=12, pady=6)

        label = tk.Label(frame, text=title, anchor="w", font=("Helvetica", 12, "bold"))
        label.pack(fill="x")

        text_widget = ScrolledText(frame, wrap="word", height=8)
        text_widget.pack(fill="both", expand=True, pady=(4, 0))
        text_widget.configure(state="disabled")
        return text_widget

    def _stream_worker(self) -> None:
        try:
            for pending in self.bot.iter_pending_replies():
                self.pending_queue.put(pending)
        except Exception as stream_error:
            logging.exception("Stream worker terminated unexpectedly")
            self.pending_queue.put(("error", stream_error))

    def _poll_queue(self) -> None:
        updated = False
        while True:
            try:
                item = self.pending_queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(item, PendingReply):
                self.pending_buffer.append(item)
                updated = True
            elif isinstance(item, tuple) and item and item[0] == "error":
                _, error = item
                messagebox.showerror(
                    "Streaming Error",
                    f"The stream terminated unexpectedly: {error}",
                )
        if (self.current_pending is None) and self.pending_buffer:
            next_pending = self.pending_buffer.pop(0)
            self._display_pending(next_pending)
            updated = True
        if not updated and self.current_pending is None:
            self.status_var.set("Waiting for new matches...")
        self.root.after(500, self._poll_queue)

    def _display_pending(self, pending: PendingReply) -> None:
        self.current_pending = pending
        self._populate_text(self.comment_text, pending.comment.body)
        self._populate_text(self.reply_text, pending.suggested_reply)
        self._populate_text(self.context_text, pending.thread_context)
        self.status_var.set(
            f"Matched keyword '{pending.matched_keyword}' for comment {pending.comment.id}"
        )
        self._set_action_buttons(True)
        self.refresh_button.configure(state=tk.NORMAL)

    def _populate_text(self, widget: ScrolledText, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="disabled")

    def _clear_display(self) -> None:
        for widget in (self.comment_text, self.reply_text, self.context_text):
            self._populate_text(widget, "")
        self.current_pending = None
        self._set_action_buttons(False)
        self.refresh_button.configure(state=tk.NORMAL)

    def _set_action_buttons(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.approve_button.configure(state=state)
        self.skip_button.configure(state=state)

    def on_approve(self) -> None:
        if not self.current_pending:
            return
        if self._posting_lock.locked():
            return
        pending = self.current_pending
        self.status_var.set(f"Posting reply to comment {pending.comment.id}...")
        self._set_action_buttons(False)
        self.refresh_button.configure(state=tk.DISABLED)

        def _poster() -> None:
            with self._posting_lock:
                try:
                    self.bot.post_reply(pending, sleep_after=False)
                    self.status_var.set(
                        f"Reply posted to comment {pending.comment.id}. Waiting for new matches..."
                    )
                except Exception as post_error:
                    logging.exception("Failed to post reply")
                    messagebox.showerror(
                        "Posting Error",
                        f"Failed to post reply: {post_error}",
                    )
                finally:
                    self.current_pending = None
                    self._clear_display()

        threading.Thread(target=_poster, name="PosterThread", daemon=True).start()

    def on_skip(self) -> None:
        if not self.current_pending:
            return
        comment_id = self.current_pending.comment.id
        self.status_var.set(f"Skipped comment {comment_id}. Waiting for new matches...")
        self.current_pending = None
        self._clear_display()

    def on_refresh(self) -> None:
        if self.current_pending is not None:
            self.status_var.set(
                f"Still reviewing comment {self.current_pending.comment.id}"
            )
            return
        if self.pending_buffer:
            next_pending = self.pending_buffer.pop(0)
            self._display_pending(next_pending)
            return
        self.status_var.set("Waiting for new matches...")

    def on_close(self) -> None:
        self.bot.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    ui = BotUI()
    ui.run()


if __name__ == "__main__":
    main()
