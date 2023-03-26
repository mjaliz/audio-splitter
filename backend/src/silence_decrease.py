import os
import pandas as pd
from pydub import AudioSegment


class SilenceDecrease:
    def __init__(self, audios_path):
        self.audios_path = audios_path
        self.audio_files = [os.path.join(self.audios_path, audio) for audio in os.listdir(audios_path)]

    def __detect_leading_silence(self, sound, silence_threshold=-50.0, chunk_size=5):
        '''
        sound is a pydub.AudioSegment
        silence_threshold in dB
        chunk_size in ms

        iterate over chunks until you find the first one with sound
        '''
        trim_ms = 0  # ms

        assert chunk_size > 0  # to avoid infinite loop
        while sound[trim_ms:trim_ms + chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
            trim_ms += chunk_size

        return trim_ms

    def export_file_size(self):
        ids = []
        sizes = []
        for a in self.audio_files:
            file_size = os.path.getsize(a)
            audio_id = os.path.splitext(os.path.basename(a))[0]
            sizes.append(file_size)
            ids.append(audio_id)

        df = pd.DataFrame(data={"id": ids, "size": sizes})
        df.to_csv('file_size.csv')

    def __trim(self, audio_file):
        sound = AudioSegment.from_file(audio_file, format="mp3")

        start_trim = self.__detect_leading_silence(sound)
        end_trim = self.__detect_leading_silence(sound.reverse())
        #
        duration = len(sound)
        trimmed_sound = sound[start_trim:duration - end_trim]

        start_silence_chunk = AudioSegment.silent(duration=50)
        end_silence_chunk = AudioSegment.silent(duration=100)

        final = start_silence_chunk + trimmed_sound + end_silence_chunk
        # final = trimmed_sound

        final.export(
            audio_file,
            bitrate="48k",
            format="mp3"
        )
        sound_du = sound.duration_seconds
        final_du = final.duration_seconds

        print(
            f"{os.path.basename(audio_file)} trimmed from {sound_du} to {final_du}, diff = {round((sound_du - final_du) * 1000, 1)}")

    def decrease_silence(self):
        for a in self.audio_files:
            self.__trim(audio_file=a)


if __name__ == '__main__':
    sd = SilenceDecrease('/home/mrph/Desktop/tmp2')
    sd.export_file_size()
    print("Done!")
