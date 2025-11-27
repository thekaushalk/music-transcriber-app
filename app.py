import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import requests
import demucs.separate
from utils.transcribe import transcribe_to_midi
from utils.midi_to_pdf import convert_midi_to_pdf
from utils.drum_transcribe import DrumBeatExtractor
from utils.midifren_wrapper import run_midifren_drums

UPLOAD_FOLDER = 'static/uploads'
OUTPUT_BASE = 'static/separated'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_BASE'] = OUTPUT_BASE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_BASE, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Clean up everything old for a fresh run
    if os.path.exists(OUTPUT_BASE):
        shutil.rmtree(OUTPUT_BASE)
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    stem = request.form.get('stem')
    stems = ["bass", "drums", "piano", "guitar", "vocals"] if stem == "all" else [stem]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Build demucs command exactly as before
        cmd = ["--mp3", "-n", "htdemucs_6s"]
        if len(stems) == 1:
            cmd += ["--two-stems", stems[0]]
        cmd.append(filepath)

        # Run Demucs separation
        demucs.separate.main(cmd)

        song_name = os.path.splitext(filename)[0]
        separated_dir = os.path.join('separated', 'htdemucs_6s', song_name)
        out_dir = os.path.join(app.config['OUTPUT_BASE'], song_name)
        os.makedirs(out_dir, exist_ok=True)

        # Move all separated files to the single output folder for this song
        if os.path.exists(separated_dir):
            for f in os.listdir(separated_dir):
                src = os.path.join(separated_dir, f)
                dst = os.path.join(out_dir, f)
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
        else:
            return f"Separation output folder not found: {separated_dir}"

        # Generate MIDI & PDF for available stems
        for s in stems:
            stem_file_mp3 = os.path.join(out_dir, f"{s}.mp3")
            stem_file_wav = os.path.join(out_dir, f"{s}.wav")
            stem_file = None
            if os.path.exists(stem_file_mp3):
                stem_file = stem_file_mp3
            elif os.path.exists(stem_file_wav):
                stem_file = stem_file_wav
            else:
                print(f"[info] stem file not found for {s}: looked for {stem_file_mp3} and {stem_file_wav}")
                continue

            if s == "drums":
                try:
                    # call the MIDIfren wrapper which runs the MIDIfren-style extraction
                    res = run_midifren_drums(
                        drum_audio_path=stem_file,
                        out_dir=out_dir,
                        sensitivity=0.45,  # tweak if needed (lower => more onsets)
                        quantize=True,
                        groove="4/4",
                        bpm=None,
                        return_debug=False
                    )
                    midi_path = res.get("midi_path")
                    if midi_path:
                        convert_midi_to_pdf(midi_path, drum_notation=True)
                except Exception as e:
                    print(f"Error processing drums: {e}")
            else:
                try:
                    midi_path = transcribe_to_midi(stem_file)
                    if midi_path and os.path.exists(midi_path):
                        convert_midi_to_pdf(midi_path)
                except Exception as e:
                    print(f"Error processing stem {s}: {e}")

        return redirect(url_for('results', song_name=song_name))
    else:
        return 'Invalid file format'

@app.route('/results/<song_name>')
def results(song_name):
    folder_path = os.path.join(app.config['OUTPUT_BASE'], song_name)
    if not os.path.exists(folder_path):
        return 'No results for this song.'
    files = os.listdir(folder_path)
    labeled_tracks = []
    for f in files:
        file_url = url_for('static', filename=f'separated/{song_name}/{f}')
        labeled_tracks.append((file_url, f))
    return render_template('results.html', song_name=song_name, labeled_tracks=labeled_tracks)

@app.route('/download/<song_name>/<filename>')
def download_file(song_name, filename):
    directory = os.path.join(app.config['OUTPUT_BASE'], song_name)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/api/get-lyrics', methods=['POST'])
def get_lyrics():
    import requests
    from bs4 import BeautifulSoup
    import re
    from flask import jsonify, request

    def clean_string(s):
        return re.sub(r"[^a-zA-Z0-9 ]", "", s).lower().strip()

    def fetch_azlyrics(artist, title):
        artist_clean = clean_string(artist).replace(" ", "")
        title_clean = clean_string(title).replace(" ", "")
        url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{title_clean}.html"

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return None

            soup = BeautifulSoup(r.text, "html.parser")

            # lyrics live inside the first large <div> after comments
            divs = soup.find_all("div")
            for div in divs:
                if div.get("class") is None and div.get("id") is None:
                    text = div.get_text("\n").strip()
                    if len(text.split()) > 20:
                        return text
            return None
        except:
            return None

    def fetch_genius_scrape(query):
        try:
            search_url = f"https://genius.com/api/search/song?q={query}"
            json_data = requests.get(search_url, timeout=10).json()
            hits = json_data["response"]["sections"][0]["hits"]
            if not hits:
                return None

            url = hits[0]["result"]["url"]
            page = requests.get(url, timeout=10).text
            soup = BeautifulSoup(page, "html.parser")

            lyrics_divs = soup.find_all("div", {"data-lyrics-container": "true"})
            if not lyrics_divs:
                return None

            lyrics = "\n".join([d.get_text("\n") for d in lyrics_divs])
            return lyrics.strip()
        except:
            return None

    # --- get user inputs ---
    data = request.get_json()
    song = (data.get("song") or "").strip()
    artist = (data.get("artist") or "").strip()

    if not song or not artist:
        return jsonify({"error": "Song and artist are required"}), 400

    # 1) Try AZLyrics
    lyrics = fetch_azlyrics(artist, song)
    if lyrics:
        return jsonify({"lyrics": lyrics})

    # 2) Try Genius fallback
    query = f"{artist} {song}"
    lyrics = fetch_genius_scrape(query)
    if lyrics:
        return jsonify({"lyrics": lyrics})

    return jsonify({"lyrics": "Lyrics not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)

