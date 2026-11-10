"""
Protect PDF - local AES-256 password protection for PDF files.

Design constraints for handling special category data:
  * Runs entirely offline. No network calls are made by this code.
  * No logging. No config files. No "recent files" list. No temp files.
  * The only file written is the protected PDF that the user explicitly
    chooses to save, via a Save As dialog.
  * Passwords and file contents are held in memory only and cleared
    (best effort) as soon as the work is done.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import PdfReadError
except Exception as exc:  # pragma: no cover
    _r = tk.Tk()
    _r.withdraw()
    messagebox.showerror("Protect PDF", f"Required components are missing:\n{exc}")
    sys.exit(1)

APP_TITLE = "Protect PDF"
MIN_PW_LEN = 8
MASK = "*"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self._build()

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"+{x}+{y}")

    def _build(self):
        frm = ttk.Frame(self, padding=16)
        frm.grid()
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="PDF to protect").grid(row=0, column=0, sticky="w")
        self.in_var = tk.StringVar()
        row1 = ttk.Frame(frm)
        row1.grid(row=1, column=0, sticky="we", pady=(2, 0))
        row1.columnconfigure(0, weight=1)
        ttk.Entry(row1, textvariable=self.in_var, state="readonly").grid(
            row=0, column=0, sticky="we"
        )
        ttk.Button(row1, text="Browse...", command=self.pick_input).grid(
            row=0, column=1, padx=(6, 0)
        )

        ttk.Label(frm, text="Password").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.pw1 = tk.StringVar()
        self.pw1_entry = ttk.Entry(frm, textvariable=self.pw1, show=MASK)
        self.pw1_entry.grid(row=3, column=0, sticky="we", pady=(2, 0))

        ttk.Label(frm, text="Confirm password").grid(
            row=4, column=0, sticky="w", pady=(8, 0)
        )
        self.pw2 = tk.StringVar()
        self.pw2_entry = ttk.Entry(frm, textvariable=self.pw2, show=MASK)
        self.pw2_entry.grid(row=5, column=0, sticky="we", pady=(2, 0))

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frm, text="Show password", variable=self.show_var, command=self.toggle_show
        ).grid(row=6, column=0, sticky="w", pady=(6, 0))

        self.go_btn = ttk.Button(frm, text="Protect PDF...", command=self.protect)
        self.go_btn.grid(row=7, column=0, sticky="we", pady=(14, 2))

        ttk.Label(
            frm,
            text="AES-256 encryption. Runs offline. Nothing is logged or stored.",
            foreground="#777",
        ).grid(row=8, column=0, sticky="w", pady=(8, 0))

    def toggle_show(self):
        ch = "" if self.show_var.get() else MASK
        self.pw1_entry.config(show=ch)
        self.pw2_entry.config(show=ch)

    def pick_input(self):
        path = filedialog.askopenfilename(
            title="Choose a PDF", filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            self.in_var.set(path)

    def protect(self):
        src = self.in_var.get().strip()
        p1 = self.pw1.get()
        p2 = self.pw2.get()
        existing = None

        if not src:
            messagebox.showwarning(APP_TITLE, "Choose a PDF first.")
            return
        if not os.path.isfile(src):
            messagebox.showerror(APP_TITLE, "That file no longer exists.")
            return
        if p1 != p2:
            messagebox.showwarning(APP_TITLE, "The two passwords do not match.")
            return
        if len(p1) < MIN_PW_LEN:
            messagebox.showwarning(
                APP_TITLE, f"Use a password of at least {MIN_PW_LEN} characters."
            )
            return

        try:
            reader = PdfReader(src)
            if reader.is_encrypted:
                existing = self._ask_existing_password()
                if existing is None:
                    return
                if not reader.decrypt(existing):
                    messagebox.showerror(
                        APP_TITLE, "That existing password was not accepted."
                    )
                    return
            writer = PdfWriter(clone_from=reader)
            writer.encrypt(user_password=p1, owner_password=None, algorithm="AES-256")
        except PdfReadError as exc:
            messagebox.showerror(APP_TITLE, f"This file could not be read as a PDF:\n{exc}")
            return
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not process the PDF:\n{exc}")
            return

        base, _ = os.path.splitext(src)
        out = filedialog.asksaveasfilename(
            title="Save protected PDF as",
            defaultextension=".pdf",
            initialfile=os.path.basename(base) + " (protected).pdf",
            initialdir=os.path.dirname(src),
            filetypes=[("PDF files", "*.pdf")],
        )
        if not out:
            return
        if os.path.abspath(out) == os.path.abspath(src):
            messagebox.showerror(
                APP_TITLE, "Choose a different name so the original is not overwritten."
            )
            return

        try:
            with open(out, "wb") as fh:
                writer.write(fh)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not save the file:\n{exc}")
            return
        finally:
            p1 = p2 = existing = None
            self.pw1.set("")
            self.pw2.set("")
            self.show_var.set(False)
            self.toggle_show()

        messagebox.showinfo(
            APP_TITLE,
            f"Protected PDF saved:\n{out}"
            "\n\nOpen it to check the password works, then securely delete the "
            "unprotected original if it is no longer needed.",
        )

    def _ask_existing_password(self):
        dlg = tk.Toplevel(self)
        dlg.title(APP_TITLE)
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(
            dlg,
            padding=14,
            text="This PDF is already password protected.\n"
            "Enter its current password to continue:",
        ).grid(row=0, column=0, columnspan=2)

        var = tk.StringVar()
        ent = ttk.Entry(dlg, textvariable=var, show=MASK, width=34)
        ent.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 12))
        ent.focus_set()

        result = {"value": None}

        def ok():
            result["value"] = var.get()
            dlg.destroy()

        def cancel():
            result["value"] = None
            dlg.destroy()

        bar = ttk.Frame(dlg, padding=(14, 0, 14, 14))
        bar.grid(row=2, column=0, sticky="e")
        ttk.Button(bar, text="Cancel", command=cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(bar, text="OK", command=ok).grid(row=0, column=1)
        ent.bind("<Return>", lambda e: ok())
        dlg.protocol("WM_DELETE_WINDOW", cancel)

        dlg.wait_window()
        return result["value"]


def _selftest() -> int:
    """In-memory check that AES-256 encryption works in this build.

    Writes nothing to disk. Prints PASS/FAIL and returns an exit code.
    """
    import io

    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    w.write(buf)
    buf.seek(0)

    enc = io.BytesIO()
    w2 = PdfWriter(clone_from=PdfReader(buf))
    w2.encrypt(user_password="selftest-password", owner_password=None, algorithm="AES-256")
    w2.write(enc)
    enc.seek(0)

    r = PdfReader(enc)
    ok = (
        r.is_encrypted
        and r.decrypt("wrong-password") == 0
        and PdfReader(enc).decrypt("selftest-password") != 0
    )

    msg = (
        "Self-test PASSED.\n\nAES-256 encryption is working on this machine."
        if ok
        else "Self-test FAILED.\n\nDo not use this build for real documents."
    )
    print(msg)
    _r = tk.Tk()
    _r.withdraw()
    (messagebox.showinfo if ok else messagebox.showerror)(APP_TITLE, msg)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    App().mainloop()
