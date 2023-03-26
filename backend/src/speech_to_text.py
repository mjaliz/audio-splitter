import whisper


class Whisper:
    def __init__(self, model_name):
        self.model_name = model_name
        self.model = whisper.load_model(model_name, device="cpu", in_memory=False,
                                        download_root="whisper_models")

    def whisper_func(self, audio_file):
        try:
            result = self.model.transcribe(audio_file)
            return result['text'].strip(" ")
        except:
            return 'invalid file'

    def speech_to_text(self, df):
        df["whisper_model"] = self.model_name
        audio_file = df["file_name"]
        audio_path = f'./audios/{audio_file}.wav'
        text = self.whisper_func(audio_path)
        df["generated_text"] = text
        print(audio_path, text)
        return df
