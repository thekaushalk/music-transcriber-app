import os
import subprocess
from pathlib import Path

def convert_midi_to_pdf(midi_path, drum_notation=False):
    """
    Convert MIDI -> PDF using MuseScore CLI.
    For drum notation, ensure the MIDI file puts drum notes on channel 10 (index 9).
    MuseScore will automatically render percussion staff for channel 10.
    """
    midi_path = str(midi_path)
    pdf_path = os.path.splitext(midi_path)[0] + ".pdf"

    # Try the common Windows install paths for MuseScore
    muse_score_bin = 'musescore3'

    cmd = [muse_score_bin, "-o", pdf_path, midi_path]
    
    try:
        _ = subprocess.run(cmd, check=True)

    except FileNotFoundError:
        print("MuseScore executable not found at expected path. Please install MuseScore 3/4 or update path in midi_to_pdf.py.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error converting MIDI to PDF: {e}")
        return None

    return pdf_path
