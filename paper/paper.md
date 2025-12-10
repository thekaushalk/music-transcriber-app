---
title: "Music Transcriber App: Automatic Music Source Separation, MIDI Transcription, and Notation Generation"
authors:
  - name: Kaushal K.
    orcid: null
    affiliation: "Independent Researcher / Student"
keywords: [Music Information Retrieval, Source Separation, Automatic Transcription, MIDI, Sheet Music, Flask, Python]
repository: "https://github.com/thekaushalk/music-transcriber-app"
license: MIT
---

# Summary

The Music Transcriber App is a Python-based web application that allows users to upload an audio file and automatically generate:

- Isolated audio stems (drums, bass, piano, guitar, vocals)
- MIDI transcriptions of each instrument
- Printable musical notation in PDF format
- Optional lyrics lookup from online sources

The app combines open-source tools—**Demucs** for source separation, **Basic Pitch** for transcription of pitched instruments, and **MIDIfren** for drum transcription—along with **MuseScore 3** for notation generation. By automating these processes, the software provides musicians, educators, and researchers with a practical tool to analyze, practice, and study music efficiently.

# Statement of Need

Existing tools for music source separation and transcription often require multiple manual steps and specialized software. Musicians and researchers seeking isolated instrument tracks and corresponding notation face time-consuming workflows.

The Music Transcriber App addresses this by integrating audio separation, MIDI transcription, and PDF notation generation in a single pipeline. Users can:

- Quickly extract and study individual instrument parts
- Generate MIDI for further computational music analysis
- Produce sheet music for practice or study without manual transcription

This software is particularly useful for **music information retrieval research**, **educational settings**, and **practical music practice**, offering a free and open-source alternative to commercial solutions.

# Workflow

The Music Transcriber App follows a clear pipeline:

1. **Audio Upload:** Users upload an audio file (`.mp3`, `.wav`, `.flac`, `.ogg`) via the web interface.  
2. **Source Separation:** **Demucs** isolates instrument stems (drums, bass, piano, guitar, vocals).  
3. **MIDI Transcription:**  
   - Non-percussive instruments are transcribed to MIDI using **Basic Pitch**.  
   - Drums are transcribed using a **librosa-based onset detection** and **MIDIfren** algorithm.  
4. **Notation Generation:** MIDI files are converted to PDF notation using **MuseScore 3**, with drum notation placed on channel 10 for proper percussion rendering.  
5. **Lyrics Lookup (Optional):** Users may fetch lyrics from AZLyrics or Genius for personal, educational, or research purposes.  

# Quality and Limitations

- The generated MIDI and PDF notation may **not be perfectly accurate**. They serve as a **point of reference** for musicians and educators.  
- **Drum transcription** is approximate; onset detection may miss or misclassify notes, and velocity dynamics may not be fully captured.  
- Source separation is generally effective but may include artifacts or bleed from other instruments.  

# Notes on Third-Party Content

- This project includes code to fetch lyrics from **Genius** and **AZLyrics**.  
- Lyrics are **copyrighted** by their respective owners.  
- The app **does not store, publish, or redistribute lyrics**.  
- Lyrics access is strictly for **personal, educational, and research purposes**, and users are responsible for complying with site Terms of Service.

# Block Diagram

![Block Diagram](paper/figures/block_diagram.png)

# App Screenshots

![App Screenshot 1](paper/figures/app_screenshot1.png)
![App Screenshot 2](paper/figures/app_screenshot2.png)
![App Screenshot 3](paper/figures/app_screenshot3.png)

# References

1. Facebook AI Research. *Demucs: Music Source Separation.* MIT License. [https://github.com/facebookresearch/demucs](https://github.com/facebookresearch/demucs)  
2. Spotify. *Basic Pitch: Automatic Music Transcription.* MIT License. [https://github.com/spotify/basic-pitch](https://github.com/spotify/basic-pitch)  
3. Omodaka. *MIDIfren: MIDI Editing and Processing Utilities.* Apache 2.0 License. [https://github.com/Omodaka9375/MIDIfren](https://github.com/Omodaka9375/MIDIfren)  
4. MuseScore. *MuseScore 3: Free Music Notation Software.* GPL v2 License. [https://musescore.org/](https://musescore.org/)  
5. McFee, B., et al. *librosa: Audio and Music Signal Analysis in Python.* Proceedings of the 14th Python in Science Conference (2015).  

# Funding

No funding was received for this project.

# Acknowledgements

This software makes use of the following open-source projects:

- **Demucs** for music source separation  
- **Basic Pitch** for pitched instrument transcription  
- **MIDIfren** for drum transcription  
- **MuseScore 3** for MIDI-to-PDF notation rendering  

# License

This repository is released under the **MIT License**. All dependencies and third-party libraries are used under their respective licenses.

# Software Availability

- **Repository:** [https://github.com/thekaushalk/music-transcriber-app](https://github.com/thekaushalk/music-transcriber-app)  
- **License:** MIT  
- **Dependencies:** Python 3.11, Flask, Demucs, Basic Pitch, MIDIfren, MuseScore 3, Librosa, NumPy, SciPy, Mido, BeautifulSoup4, Requests
