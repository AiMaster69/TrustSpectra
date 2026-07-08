# TrustSpectra

**TrustSpectra** is a desktop application for automatically detecting specific audio patterns in audio files. The program uses local neural network models to analyze audio tracks and identifies fragments featuring characteristic intimate acoustic patterns.

🔒 **Core principle:** Fully offline mode. Your files never leave your computer; no data is sent to external servers.

---

## ⚠️ Important Information

> **Beta version and AI capabilities**
> The program is under active development. It relies on machine learning algorithms which are not infallible: false positives and missed fragments may occur. Analysis results **require mandatory manual verification**.
>
> **Ethics and legality**
> The program analyzes exclusively the files you upload yourself. Usage is permitted only for files you have the rights to, or those recorded with the consent of the participants. Use for covert surveillance or privacy violations is strictly prohibited. The author assumes no liability for the unlawful use of this software.

---

## 🎯 Features

* **Smart detection:** Automatically finds intimate audio fragments.
* **Precise timestamps:** Identifies the exact start and end times of each detected fragment.
* **Flexible tuning:** Adjustable sensitivity threshold (from 0.0 to 1.0) per audio type.
* **Large file support:** Optimized algorithm for analyzing long-duration recordings.
* **Absolute privacy:** No microphone recording, no cloud, strictly local processing.

---

## 💻 System Requirements
* **OS:** Windows 10/11 64-bit
* **RAM:** Minimum 8 GB
* **GPU:** Not required (runs exclusively on CPU)
* **Disk space:** ~200 MB for installation + space for temporary files.

---

## 📥 Installation

### For end users (ready-to-use installer)
1. Go to the **Releases** tab (on the right side of this page) or download the latest `TrustSpectra-Setup.exe` (~117 MB) via the [direct link]().
   > *Note: The large file size is because all offline models and audio processing libraries are embedded. No additional internet download is required.*
2. Run `TrustSpectra-Setup.exe` and follow the installer instructions.
3. Open the app, click **"Load Audio"** (supports `.mp3`, `.wav`, `.ogg`, `.flac`).
4. **Adjust sensitivity:** in the side panel, change the confidence threshold (higher means stricter detection).
5. **Run the analysis** and wait for it to complete.
6. **Review the results:** click on any timestamp in the list to preview the found fragment.

### 🧑‍💻 For developers (run from source)
If you want to run the program directly from the code:
1. Clone the repository: `git clone https://github.com/AiMaster69/TrustSpectra.git`
2. Navigate to the project folder: `cd TrustSpectra`
3. Install dependencies and set up the environment with a single command: `make setup`
4. Run the application: `make run`

---

## 🛠️ Tech Stack & Dependencies

The project uses the following libraries (minimum versions specified):

**UI & File handling:**
* `PyQt6` >= 6.0.0
* `numpy` >= 1.21.0
* `sounddevice` >= 0.4.6
* `soundfile` >= 0.12.1
* `mutagen` >= 1.45.1

**AI & Audio Processing:**
* `onnxruntime` >= 1.16.0
* `librosa` >= 0.10.0
* `scipy` >= 1.9.0

---

## 💬 Feedback & Bug Reports

If you've found a bug or have a suggestion, please join our **[Discord server](your_discord_invite_link_here)**.

> **Important:** I personally review and handle all bug reports and feedback exclusively through Discord. Please use the appropriate channel there for technical support. GitHub Issues are not monitored for this project.

---

## 📜 License

This project is distributed under the [MIT](LICENSE) license.
