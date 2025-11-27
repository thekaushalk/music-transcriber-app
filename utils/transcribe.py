import os
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

def transcribe_to_midi(audio_path):
    output_dir = os.path.dirname(audio_path)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    midi_path = os.path.join(output_dir, f"{base_name}_basic_pitch.mid")

    predict_and_save(
        [audio_path],
        output_directory=output_dir,
        model_or_model_path=ICASSP_2022_MODEL_PATH,
        sonify_midi=False,
        save_midi=True,
        save_model_outputs=False,
        save_notes=False
    )

    return midi_path
