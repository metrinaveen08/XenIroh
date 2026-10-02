# XenIroh

<p align="center">
  <b>Explainable-AI static file analysis for Windows</b>
</p>

<p align="center">
  A cybersecurity/AI project that watches your files, analyzes them without executing them, and explains why something looks suspicious.
</p>

<br>

## Installation is easy!

### Requirements

* Windows 10/11
* Python 3.13
* Conda
* PyQt5

### Install from source

1. Clone the repository:

```bash
git clone https://github.com/metrinaveen08/XenIroh.git
cd XenIroh
```

2. Create the environment:

```bash
conda create -n xeniroh python=3.13
conda activate xeniroh
```

3. Install the requirements:

```bash
pip install -r requirements.txt
```

4. Run XenIroh:

```bash
python main.py
```

On the first run XenIroh will ask which folders you want it to watch.

---

## What is XenIroh?

XenIroh is a project built around **cybersecurity, static analysis and explainable AI**.

The idea is to analyze a file without running it, collect useful evidence from it, and then use that evidence to produce a result that can actually be understood.

Instead of only saying:

```text
Suspicious
```

XenIroh tries to show **why** it reached that result.

```text
File
  ↓
Static Analysis
  ↓
Evidence
  ↓
Rules / AI
  ↓
Verdict
  ↓
Explanation
```

---

## What can it analyze?

### Files

* File type
* MD5
* SHA-1
* SHA-256
* Suspicious strings
* Windows PE files
* PE sections
* PE entropy
* Imported APIs
* UPX/packing indicators
* Office VBA macros
* PDF JavaScript

### Images

* Image format
* Dimensions
* EXIF metadata
* Data after EOF markers
* LSB entropy
* Possible steganography indicators

XenIroh does **not execute the file** during analysis.

---

## Background monitoring

XenIroh can run in the system tray and watch folders in the background.

When a new file appears:

1. XenIroh detects it.
2. It waits until the file stops changing.
3. The appropriate analyzer is selected.
4. Evidence is collected.
5. The reasoning layer evaluates the evidence.
6. The result is shown through the tray notification.

`watchdog` is used for filesystem monitoring, with a polling fallback.

Temporary files such as `.crdownload`, `.part` and `.tmp` are ignored.

---

## There's more than just the scanner

### Security Chat

A small local chat interface for interacting with the analysis information.

### Rules

XenIroh has a separate rules system for its protection logic.

Private rules can be protected using a password and stored separately from the normal configuration.

### Themes

Currently available:

* Green / White
* Dark Emerald
* Light Clean

### Settings

The current settings allow you to manage:

* Watched folders
* Windows startup
* Quarantine

The settings system is also being extended to separate:

* General
* Watchdog Directories
* Rules
* Appearance
* Quarantine
* About

### Quarantine

Suspicious files can be moved into XenIroh's quarantine directory instead of being left in their original location.

The quarantine can also be cleared from the application.

---

## How the analysis works

The actual analysis is split into different parts of the project.

```text
Assets/Analyzers/
```

contains the file and image analyzers.

```text
Assets/AiConnector/
```

connects the collected evidence to the reasoning layer.

```text
Ai/
```

contains the reasoning, probability and rule-related code.

The final result contains:

```text
Verdict
Evidence
Reasoning
Conclusion
```

The current verdicts are:

* `Suspicious`
* `Likely Safe`
* `Inconclusive`

These are based on the indicators XenIroh currently checks and should not be treated as a guarantee that a file is malicious or safe.

---

## Project structure

```text
XenIroh/
├── Ai/
│   ├── chatandagents/
│   │   ├── agent.py
│   │   ├── chat.py
│   │   └── logic.py
│   │
│   └── probabilityandrules/
│       ├── probability.py
│       ├── rules_advisor.py
│       └── search.py
│
├── AppGUI/
│   ├── mainApp/
│   │   ├── App.py
│   │   ├── chatpage.py
│   │   ├── rulespage.py
│   │   ├── settings.py
│   │   ├── setup.py
│   │   └── themespage.py
│   │
│   └── TrayApp/
│       └── trayapp.py
│
├── Assets/
│   ├── AiConnector/
│   │   └── aibridge.py
│   │
│   └── Analyzers/
│       ├── FileAnalyzer.py
│       └── ImageAnalyzer.py
│
├── StartupAndWatcher/
│   ├── startup.py
│   └── watcher.py
│
├── config/
│   ├── permissions.py
│   ├── protection.py
│   ├── rules.py
│   └── settings.py
│
├── main.py
└── requirements.txt
```

---

## There's no sandbox here

XenIroh originally had the idea of using a Windows sandbox for dynamic analysis.

That direction was dropped.

The current project is focused on **static analysis** instead.

This means XenIroh reads the file and analyzes its structure and contents, but doesn't run the file inside a sandbox.

---

## Why?

I wanted to build something that combines the things I'm learning in **AI/ML and cybersecurity** into an actual working project.

The interesting part for me isn't just detecting something.

It's being able to look at the result and ask:

> What did it find?

> Why does that matter?

> Why did the system reach this conclusion?

That's the part XenIroh is built around.

---

## Current status

| Part                           | Status |
| ------------------------------ | ------ |
| File analysis                  | ✅      |
| Image analysis                 | ✅      |
| Hashing                        | ✅      |
| PE analysis                    | ✅      |
| Macro analysis                 | ✅      |
| PDF JavaScript detection       | ✅      |
| Suspicious string detection    | ✅      |
| Image steganography indicators | ✅      |
| Explainable reasoning          | ✅      |
| Background watcher             | ✅      |
| System tray                    | ✅      |
| Windows startup                | ✅      |
| First-run setup                | ✅      |
| Rules system                   | ✅      |
| Password-protected rules       | ✅      |
| Quarantine                     | ✅      |
| Themes                         | ✅      |
| Security Chat                  | ✅      |
| Settings                       | 🚧     |
| Dedicated Settings submenus    | 🚧     |

---

## Notes

XenIroh is still a project under development.

It is **not an antivirus replacement** and shouldn't be treated as one.

The analysis is based on the indicators currently implemented in XenIroh, so a `Likely Safe` result doesn't guarantee that a file is safe, and a `Suspicious` result doesn't automatically mean that the file is malware.

The goal is to keep improving the analysis, reasoning and explainability while keeping the project understandable and usable.

---

## License

GNU GPLv3.

```text
Copyright (C) 2026 Metri Naveen Kumar (Xenon Akro)
```
