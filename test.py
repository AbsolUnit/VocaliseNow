from TTS.api import TTS
api = TTS(model_name="tts_models/eng/fairseq/vits", gpu=True)
api.tts_to_file("This is a test.", file_path="output.wav")