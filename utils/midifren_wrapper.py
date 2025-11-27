import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from .drum_transcribe import DrumBeatExtractor, quantize_midi_file
import mido

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_midifren_drums(
    drum_audio_path: str,
    out_dir: str,
    sensitivity: float = 0.45,
    quantize: bool = True,
    groove: str = "4/4",
    bpm: Optional[int] = None,
    return_debug: bool = False
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extractor = DrumBeatExtractor()
    if bpm is None:
        bpm = extractor.detect_tempo(drum_audio_path)

    midi_path_generated = extractor.extract_midi(
        drum_audio_path,
        tempo=bpm,
        sensitivity=sensitivity,
        groove=groove,
        quantize=quantize,
        web=False
    )

    if not midi_path_generated:
        return {"midi_path": None, "pdf_path": None, "debug": None}

    midi_generated_path = Path(midi_path_generated)
    midi_final = out_dir / "drums.mid"
    try:
        if midi_generated_path.resolve() != midi_final.resolve():
            if midi_final.exists():
                midi_final.unlink()
            shutil.move(str(midi_generated_path), str(midi_final))
    except Exception:
        if not midi_final.exists() and midi_generated_path.exists():
            shutil.copy(str(midi_generated_path), str(midi_final))

    if quantize:
        try:
            tmp = out_dir / "drums.quant_tmp.mid"
            quantize_midi_file(str(midi_final), str(tmp), bpm, subdivision=4)
            shutil.move(str(tmp), str(midi_final))
        except Exception:
            print("[midifren_wrapper] quantize pass failed; continuing")

    midi_str = str(midi_final) if midi_final.exists() else None
    pdf_str = None

    debug_list = None
    if return_debug and midi_str:
        import mido as _mido
        debug_list = []
        mid = _mido.MidiFile(midi_str)
        for tr_idx, track in enumerate(mid.tracks):
            abs_t = 0
            for msg in track:
                abs_t += msg.time
                if msg.type == "note_on":
                    debug_list.append({"track": tr_idx, "abs_time_ticks": abs_t, "channel": getattr(msg, "channel", None), "note": getattr(msg, "note", None), "velocity": getattr(msg, "velocity", None)})
    return {"midi_path": midi_str, "pdf_path": pdf_str, "debug": debug_list}
