<div align="center">

# DOWNSORT // MK-I
### Autonomous, Event-Driven Download Organizer & File Telemetry HUD

![Python](https://img.shields.io/badge/Python-3.10%2B-00f3ff?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-00ff9d?style=for-the-badge)
![Memory](https://img.shields.io/badge/RAM_Footprint-~20_MB-ffb700?style=for-the-badge)

**Zero-bloat file automation built for speed, low memory overhead, and uninterrupted browser downloads.**

</div>

---

## Overview

Most file-sorting scripts rely on infinite polling loops that waste CPU cycles, restrict sorting to a hardcoded list of extensions, or crash active browser downloads by moving half-written files.

**DownSort** solves all three problems. Built with Python 3, `watchdog`, and a custom dark sci-fi `tkinter` interface, it hooks directly into native Windows OS file-system events (`ReadDirectoryChangesW`) to stay at **0% idle CPU** while organizing incoming files the millisecond they finish downloading.

---

## Core Capabilities

- **Unrestricted Dynamic Extension Routing:** Automatically detects any file extension (`.pdf`, `.zip`, `.mp4`, `.exe`, `.py`, `.iso`, etc.) and generates dedicated uppercase directories on the fly—no manual rule configuration required.
- **Partial-Download Staging & Auto-Cleanup:** Identifies active browser temporary files (`.crdownload`, `.part`, `.tmp`, `.download`), keeps the original file untouched so active downloads never corrupt, maintains a live snapshot in `_In_Progress_Copies/`, and deletes the staged copy the instant the download finishes.
- **Collision-Safe File Handling:** Detects naming conflicts in target folders and resolves them deterministically (`document.pdf` $\rightarrow$ `document_1.pdf`) so existing files are never overwritten.
- **Zero-Polling Event Architecture:** Powered by `watchdog` OS-level hooks rather than `while True` directory scans, keeping background RAM usage around **~20 MB**.
- **Tactical Sci-Fi HUD:** Minimalist obsidian-and-cyan interface featuring an animated scanner ring, live telemetry counters, color-coded event logs, and instant Pause/Scan controls.
- **One-Click Silent Boot Integration:** Generates a windowless VBScript launcher inside Windows `shell:startup` (`--minimized`) for effortless background execution on system startup.

---

## System Architecture

```text
Downloads Directory (OS Kernel Event: ReadDirectoryChangesW)
       │
       ├──► [Created / Modified] ──► Is Partial Extension (.crdownload / .part / .tmp)?
       │                                  ├── YES ──► Copy Snapshot to _In_Progress_Copies/
       │                                  └── NO  ──► Create /<EXT>/ Folder ──► Safe Move
       │
       └──► [Renamed / Completed] ─► Delete Staged Copy from _In_Progress_Copies/
                                          └──► Route Final File to /<EXT>/ Folder
