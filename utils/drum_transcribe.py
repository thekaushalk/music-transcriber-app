import os
from pathlib import Path
import numpy as np
import librosa
import mido
import math
import shutil

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def quantize_midi_file(input_path, output_path, bpm, subdivision=4):
    mid = mido.MidiFile(input_path)
    new_mid = mido.MidiFile()
    new_mid.ticks_per_beat = mid.ticks_per_beat

    for track in mid.tracks:
        new_track = mido.MidiTrack()
        current_time = 0
        events = []
        # convert to absolute times
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            events.append((abs_time, msg.copy()))

        # quantize note_on/note_off absolute times
        resolution_ticks = max(1, mid.ticks_per_beat // subdivision)
        for i, (t, msg) in enumerate(events):
            if msg.type in ['note_on', 'note_off']:
                q = round(t / resolution_ticks) * resolution_ticks
                events[i] = (int(q), msg)

        # sort and convert back to delta
        events.sort(key=lambda x: x[0])
        last = 0
        for t, msg in events:
            delta = int(max(0, t - last))
            last = t
            m = msg.copy()
            m.time = delta
            new_track.append(m)
        new_mid.tracks.append(new_track)

    new_mid.save(output_path)

class DrumBeatExtractor:
    def __init__(self):
        self.y = None
        self.sr = None
        self.onset_frames = None
        self.drum_types = None

    def detect_tempo(self, audio_file):
        try:
            y, sr = librosa.load(audio_file, sr=None, mono=True)
            yt, index = librosa.effects.trim(y)
            tempo, _ = librosa.beat.beat_track(y=yt, sr=sr, units="time")
            tempo_int = int(tempo) if tempo and not math.isnan(tempo) else 120
            print(f"Detected tempo: {tempo_int} BPM")
            return max(20, tempo_int)
        except Exception as e:
            print(f"Error detecting tempo: {e}")
            return 120

    def extract_midi(self, audio_file, tempo, sensitivity, groove, quantize, web):
        times = groove.split('/')
        nom = int(times[0]) if len(times) > 0 else 4
        denom = int(times[1]) if len(times) > 1 else 4

        try:
            process_dir = OUTPUT_DIR / str(hash(audio_file))
            process_dir.mkdir(parents=True, exist_ok=True)
            out_folder_path = Path("output")
            out_folder_path.mkdir(parents=True, exist_ok=True)

            self.y, self.sr = librosa.load(audio_file, sr=None, mono=True)
            yt, index = librosa.effects.trim(self.y)
            y_normalized = librosa.util.normalize(yt)

            y_percussive = librosa.effects.percussive(y_normalized)

            hop_length = 512
            onset_env = librosa.onset.onset_strength(
                y=y_percussive,
                sr=self.sr,
                hop_length=hop_length,
                aggregate=np.median
            )

            wait_time = 0.04
            delta_time = sensitivity
            pre_avg_time = 0.1
            pre_max_time = 0.03

            wait_frames = max(0, int(wait_time * self.sr / hop_length))
            pre_avg_frames = max(0, int(pre_avg_time * self.sr / hop_length))
            pre_max_frames = max(0, int(pre_max_time * self.sr / hop_length))

            self.onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_env,
                sr=self.sr,
                hop_length=hop_length,
                backtrack=True,
                units='frames',
                wait=wait_frames,
                delta=delta_time,
                pre_avg=pre_avg_frames,
                post_avg=1,
                pre_max=pre_max_frames,
                post_max=1
            )

            onset_times = librosa.frames_to_time(self.onset_frames, sr=self.sr, hop_length=hop_length)

            self.drum_types = []
            n_mfcc = 13

            for i, frame in enumerate(self.onset_frames):
                start_sample = frame * hop_length
                segment_duration = 0.1
                end_sample = min(len(y_normalized), start_sample + int(segment_duration * self.sr))
                if start_sample >= end_sample:
                    continue

                segment = y_normalized[start_sample:end_sample]
                if len(segment) == 0:
                    continue

                spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=self.sr)[0].mean()
                spectral_bandwidth = librosa.feature.spectral_bandwidth(y=segment, sr=self.sr)[0].mean()
                rms = np.sqrt(np.mean(segment**2))
                zero_crossing_rate = librosa.feature.zero_crossing_rate(y=segment)[0].mean()
                mfccs = librosa.feature.mfcc(y=segment, sr=self.sr, n_mfcc=n_mfcc)
                mfcc1_mean = mfccs[0].mean() if mfccs.size else 0.0

                kick_rms_thresh = 0.03
                kick_spec_cent_thresh = 1200
                kick_spec_bw_thresh = 1800
                kick_mfcc1_thresh = -150

                snare_rms_thresh = 0.03
                snare_spec_bw_thresh = 2500
                snare_zcr_thresh = 0.08

                hat_spec_cent_thresh = 2500
                hat_zcr_thresh = 0.15

                if (rms > kick_rms_thresh and
                    spectral_centroid < kick_spec_cent_thresh and
                    spectral_bandwidth < kick_spec_bw_thresh and
                    mfcc1_mean > kick_mfcc1_thresh):
                    drum_type = 36
                elif (zero_crossing_rate > hat_zcr_thresh and
                      spectral_centroid > hat_spec_cent_thresh):
                    drum_type = 42
                elif (rms > snare_rms_thresh and
                      spectral_bandwidth > snare_spec_bw_thresh and
                      zero_crossing_rate > snare_zcr_thresh):
                    drum_type = 38
                else:
                    if rms > kick_rms_thresh * 1.5:
                        drum_type = 36
                    else:
                        drum_type = 38

                self.drum_types.append(drum_type)

        except Exception as e:
            print(f"Error analyzing audio: {e}")
            return None

        try:
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            mid.tracks.append(track)

            tempo_in_microseconds = mido.bpm2tempo(tempo)
            track.append(mido.MetaMessage('set_tempo', tempo=tempo_in_microseconds))
            track.append(mido.MetaMessage('time_signature', numerator=nom, denominator=denom))

            ticks_per_beat = mid.ticks_per_beat
            seconds_per_tick = 60.0 / (tempo * ticks_per_beat)

            onset_times = librosa.frames_to_time(self.onset_frames, sr=self.sr, hop_length=hop_length)

            last_tick = 0
            for i, onset_time in enumerate(onset_times):
                tick = int(onset_time / seconds_per_tick)
                delta_time = tick - last_tick
                last_tick = tick

                if i < len(self.drum_types):
                    note = self.drum_types[i]
                    track.append(mido.Message('note_on', note=note, velocity=100, time=delta_time, channel=9))
                    track.append(mido.Message('note_off', note=note, velocity=0, time=10, channel=9))

            if web:
                midi_path = process_dir / "drums.mid"
            else:
                midi_path = out_folder_path / "drums.mid"

            midi_path = Path(midi_path)
            midi_path.parent.mkdir(parents=True, exist_ok=True)
            mid.save(str(midi_path))

            if quantize:
                tmp = midi_path.with_suffix('.quant_tmp.mid')
                quantize_midi_file(str(midi_path), str(tmp), bpm=tempo, subdivision=4)
                shutil.move(str(tmp), str(midi_path))

            return str(midi_path)

        except Exception as e:
            print(f"Error exporting MIDI: {e}")
            return None
