# Protect PDF

A tiny desktop app that adds **AES-256 password protection** to a PDF file. It runs
entirely on your machine with a simple Tkinter interface — pick a PDF, set a
password, and save a protected copy.

It was built with handling sensitive / special-category documents in mind:

- **Runs entirely offline.** No network calls are made by the app.
- **No logging, no config files, no "recent files" list, no temp files.**
- The only file written is the protected PDF you explicitly choose to save,
  via a *Save As* dialog.
- Passwords and file contents are held in memory only and cleared (best effort)
  as soon as the work is done.

## Features

- AES-256 encryption (via [`pypdf`](https://pypdf.readthedocs.io/) +
  [`cryptography`](https://cryptography.io/)).
- Password confirmation and a minimum length check (8 characters).
- Handles PDFs that are **already** encrypted — prompts for the current password
  before re-protecting.
- Refuses to overwrite the original file.
- Built-in self-test to confirm encryption works on your machine.

## Requirements

- Python 3.11+ (built and tested on 3.14)
- See [`requirements.txt`](requirements.txt)

## Run from source

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python protect_pdf.py
```

## Self-test

Confirms AES-256 encryption is working without touching any of your files:

```bash
python protect_pdf.py --selftest
```

## Build a standalone Windows .exe

The app is distributed as a single `.exe` built with
[PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Protect PDF" protect_pdf.py
```

The executable will be created in `dist/`.

> **Note on antivirus warnings:** unsigned one-file PyInstaller executables are
> frequently flagged by browsers and antivirus software, and recipients will see
> "unknown publisher" prompts. Running from source (above) avoids this. For wider
> distribution, consider code-signing the executable.

## Usage

1. Click **Browse...** and choose a PDF.
2. Enter a password and confirm it.
3. Click **Protect PDF...** and choose where to save the protected copy.
4. Open the saved file to confirm the password works, then securely delete the
   unprotected original if it is no longer needed.

## License

No license is set yet. Until you add one, default copyright applies (all rights
reserved). If you want others to reuse it, add a `LICENSE` file — [MIT](https://choosealicense.com/licenses/mit/)
is a common permissive choice.
