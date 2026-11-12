"""Local sign-in window; credentials are handled by the official W&B SDK."""
import contextlib
import io
import queue
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser


def main():
    root = tk.Tk()
    root.title("Connect this computer to W&B")
    root.geometry("570x310")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Sign in to Weights & Biases", font=("Segoe UI", 15)).pack(anchor="w")
    ttk.Label(frame, text="1. Open W&B, sign in, and create or copy your API key.").pack(anchor="w", pady=(16, 5))
    ttk.Button(frame, text="Open W&B authorization page", command=lambda: webbrowser.open("https://forge.coreweave.com/wandb/authorize?ref=models")).pack(anchor="w")
    ttk.Label(frame, text="2. Paste only the key below, then click Connect.").pack(anchor="w", pady=(16, 5))
    key_box = ttk.Entry(frame, show="*", width=70)
    key_box.pack(fill="x")
    status = tk.StringVar(value="Your key stays on this computer. Do not send it in chat.")
    ttk.Label(frame, textvariable=status, wraplength=525).pack(anchor="w", pady=10)
    results = queue.Queue()

    def worker(key):
        # Never display SDK exceptions or captured output, which may contain credentials.
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                import wandb
                success = wandb.login(key=key, verify=True, prompt=False)
            results.put("Connected successfully. You can close this window and tell me in chat." if success else "Sign-in did not complete. Please check the key and try again.")
        except Exception:
            results.put("Could not verify the key. Check that it is a W&B API key and that your internet connection works.")
        finally:
            key = None

    def connect():
        key = key_box.get().strip()
        if not key or any(c.isspace() for c in key) or "://" in key:
            status.set("Paste only the API key, without a web address, quotes, or spaces.")
            return
        key_box.delete(0, "end")
        button.configure(state="disabled")
        status.set("Checking your sign-in. Please wait...")
        threading.Thread(target=worker, args=(key,), daemon=True).start()
        root.after(150, poll)

    def poll():
        try:
            status.set(results.get_nowait())
            button.configure(state="normal")
        except queue.Empty:
            root.after(150, poll)

    button = ttk.Button(frame, text="Connect", command=connect)
    button.pack(anchor="w")
    root.mainloop()


if __name__ == "__main__":
    main()
