# XenIroh
 
XenIroh is an academic cybersecurity /explainable-AI project that watches for suspicious files on a
Windows PC, statically analyzes them without ever executing them, and explains — in
plain terms, with evidence and reasoning — why a file looks safe or suspicious. The AI
layer is yet to be implemented
 
> **Sandbox = what happened. AI = what does it mean.**
> Static analysis and the background watcher collect evidence. `AI/agent.py` reasons
> over that evidence and produces an explainable verdict.
 
---
 
## What it actually does
 
1. XenIroh installs and runs as a background application — a system tray icon, started
   automatically at Windows login.
2. On first run, it asks which folders to watch (Downloads and Desktop are suggested;
   any custom folder can be added).
3. Whenever a new file lands in a watched folder, XenIroh waits for it to finish
   writing, then statically analyzes it — file type, hashes, PE/macro/PDF structure,
   suspicious strings, image metadata, and steganography indicators.
4. That evidence is handed to the AI layer, which returns a verdict (**Suspicious**,
   **Likely Safe**, or **Inconclusive**) along with the evidence and reasoning behind it.
5. If a file is flagged, a tray notification appears. Opening it shows the full
   explainable report, with an option to delete the file.
6. A file can also be dropped onto or chosen in the manual analyzer window at any time,
   without waiting for the background watcher.
XenIroh never executes, opens, or renders the content of a file as part of analysis —
only its raw bytes and structure are read.
 
## What it deliberately does *not* do
 
- **No sandboxed execution.** An earlier direction explored a Windows-native sandbox
  (AppContainer / Restricted Tokens / Job Objects) for controlled dynamic analysis.
  That was dropped to fit the project timeline
  Everything in the current build is static analysis only.
- **No external AI.** No OpenAI/Claude/Gemini/Hugging Face/pretrained classifiers. The
  reasoning layer is implemented from scratch using syllabus concepts (Units I–V:
  search, logic, planning, probability/learning).
- **No message-content interception.** XenIroh does not read inside apps like
  WhatsApp/Telegram/email — it reacts to files that land on disk in a watched folder,
  however they got there.
- **No claim of hardened isolation.** This is a lightweight, explainable static-analysis
  tool for an academic setting, not a hardened malware sandbox or antivirus replacement.
## Project status
 
| Layer | Status |
|---|---|
| Static file analysis (`Assets/FileAnalyzer.py`) | ✅ Built |
| Static image analysis (`Assets/ImageAnalyzer.py`) | ✅ Built |
| AI ↔ analysis bridge (`Assets/AiBridge.py`) | ✅ Built |
| Least-privilege file handling (`DevicePermissions/`) | ✅ Built |
| Settings persistence (`Config/settings.py`) | ✅ Built |
| Startup registration (`Startup/startup.py`) | ✅ Built |
| Background folder watcher (`Watcher/watcher.py`) | ✅ Built |
| Manual analyzer window (`GUI/XenIroh.py`) | ✅ Built |
| First-run setup dialog (`GUI/SetupDialog.py`) | ✅ Built |
| System tray app (`GUI/TrayApp.py`) | ✅ Built |
| **AI reasoning layer (`AI/agent.py`, `search.py`, `logic.py`, `probability.py`)** | ⏳ Not yet implemented — the core academic deliverable |
| Native sandbox / dynamic analysis | ❌ Out of scope (dropped) |
 
Every part above the AI layer already calls into a single function,
`AI.agent.evaluate(evidence)`. Until that function exists, XenIroh runs end-to-end and
reports every file as **Inconclusive** — so the whole pipeline can be tested before the
AI logic is written.
 
See `XenIroh_Code_Reference.pdf` (generated separately) for a function-by-function
walkthrough of every module and how they call each other.
 
## Architecture
 
```text
                         XenIroh
                            |
          +-----------------+-----------------+
          |                 |                 |
         GUI        Static Analysis      Background Watcher
   (Tray + manual          |            (watches chosen folders,
     analyzer)              |             auto-triggers analysis)
          |                 |                 |
          +--------+--------+--------+--------+
                            |
                    Evidence / Observations
                            |
                            v
                        XenIroh AI
                            |
            +---------------+---------------+
            |               |               |
          Search           Logic      Probability/Learning
            |               |               |
            +---------------+---------------+
                            |
                            v
                    Explainable Result
                    (verdict + evidence + reasoning)
```
 
## Repository structure
 
```text
XenIroh/
├── AI/                     # AI reasoning layer — implement against the syllabus
│   ├── agent.py            #   evaluate(evidence) -> verdict/evidence/reasoning/conclusion
│   ├── search.py           #   Unit I search algorithms
│   ├── logic.py             #   Unit II/III propositional & FOL reasoning
│   └── probability.py       #   Unit V uncertainty/Bayesian reasoning
│
├── Assets/
│   ├── FileAnalyzer.py      # static analysis: hashes, PE, macros, PDF, strings
│   ├── ImageAnalyzer.py     # static analysis: EXIF, trailing data, LSB entropy
│   └── AiBridge.py          # single call site into AI/agent.py + report formatting
│
├── Config/
│   └── settings.py          # persisted settings (watched folders, startup pref)
│
├── DevicePermissions/
│   └── permissions.py       # least-privilege, read-only file access helpers
│
├── GUI/
│   ├── TrayApp.py           # always-on tray app; owns the background watcher
│   ├── SetupDialog.py       # first-run / settings: choose folders to watch
│   └── XenIroh.py           # manual analyzer window
│
├── Startup/
│   └── startup.py           # per-user Windows login startup registration
│
├── Watcher/
│   └── watcher.py           # background filesystem monitoring (watchdog)
│
├── Sandbox/                 # unused — dynamic-analysis sandbox was dropped
├── main.py                  # entry point — launches the tray app
├── requirements.txt
└── README.md
```
 
## Requirements
 
- Windows 10/11
- [Conda](https://docs.conda.io/) (preferred over venv for this project)
- Python 3.13.15, in a conda environment named `xeniroh`
- PyQt5 for the GUI
```bash
conda create -n xeniroh python=3.13.15
conda activate xeniroh
pip install -r requirements.txt
```
 
`requirements.txt` includes:
 
- `PyQt5` — GUI and system tray
- `watchdog` — background folder monitoring
- `Pillow` — image analysis
- `pefile` — PE executable structure
- `oletools` — Office macro analysis
- `PyMuPDF` — PDF structure analysis
- `python-magic-bin` *(Windows)* — file-type detection by content, not extension
- utility/data libraries used by static analysis and future AI work (`numpy`,
  `pandas`, `cryptography`, etc.)
> **Known issue:** if PyQt5 fails with `ImportError: DLL load failed`, check for a
> stray `python-qt5` package (`pip uninstall python-qt5`) or a conflicting Qt install
> from another package (e.g. `opencv-python`, which should be swapped for
> `opencv-python-headless`), then `pip install --force-reinstall --no-cache-dir PyQt5`.
 
## Running it
 
```bash
conda activate xeniroh
python main.py
```
 
On first launch, a setup dialog appears to choose which folders to watch. After that,
XenIroh minimizes to the system tray and runs in the background, starting automatically
at login (per-user, no admin rights required).
 
Right-click the tray icon for:
 
- **Open XenIroh** — manual analyzer window
- **Settings...** — change watched folders / startup preference
- **Pause / Resume Monitoring**
- **Quit XenIroh**
Double-click the tray icon to open the report for the most recently flagged file.
 
## Implementing the AI layer
 
Everything above the AI layer is already wired to call exactly one function. To bring
XenIroh's verdicts to life, implement this in `AI/agent.py`:
 
```python
def evaluate(evidence: dict) -> dict:
    return {
        "verdict": "Suspicious" | "Likely Safe" | "Inconclusive",
        "evidenceSummary": [...],   # short strings describing key evidence
        "reasoningSummary": [...], # short strings describing the reasoning steps
        "conclusion": "...",        # one-paragraph plain-English explanation
    }
```
 
`evidence` is exactly the dict produced by `Assets/FileAnalyzer.analyzeFile()` or
`Assets/ImageAnalyzer.analyzeImage()`. `AI/search.py`, `AI/logic.py`, and
`AI/probability.py` are where the individual syllabus algorithms should live;
`AI/agent.py` orchestrates them into the final `evaluate()` result.
 

## License
 
GNU GPLv3.
 
```text
Copyright (C) 2026 Metri Naveen Kumar (Xenon Akro)
```
 

 
