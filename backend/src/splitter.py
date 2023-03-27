import time

from pydub import AudioSegment
from pydub.silence import split_on_silence
from speech_to_text import Whisper
import pandas as pd
import os
import requests
from difflib import SequenceMatcher
import json


class Splitter:
    def __init__(self, env, examples_type, access_token, input_uid, audio_format, target_db_fs, audio_file=None,
                 min_silence_len=600,
                 silence_thresh=-50,
                 silence_padding=100):
        self.env = env
        self.examples_type = examples_type
        self.access_token = access_token
        self.input_uid = input_uid
        self.audio_format = audio_format
        self.target_dBFS = target_db_fs
        self.audio_file = audio_file
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.silence_padding = silence_padding
        self.audios_list = []
        self.texts_list = []
        self.validated_srcs = []
        self.uploaded_audios = {}
        self.current_path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(self.current_path, "..", "input", input_uid)
        self.output_path = os.path.join(self.current_path, "..", "output", input_uid)
        self.stt = Whisper('tiny.en')

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

    def __decrease_silence(self, output_dir):
        audio_files = [os.path.join(output_dir, audio) for audio in os.listdir(output_dir)]
        for a in audio_files:
            self.__trim(audio_file=a)

    def __add_files(self, src_dir, files_list):
        if os.path.isdir(src_dir):
            files = os.listdir(src_dir)
            for file in files:
                file_full_name = os.path.join(src_dir, file)
                if os.path.isfile(file_full_name):
                    files_list.append(file_full_name)

    def __get_input_files(self):
        self.__add_files(os.path.join(self.input_path, "audio"), self.audios_list)
        self.__add_files(os.path.join(self.input_path, "text"), self.texts_list)

    def __match_target_amplitude(self, a_chunk):
        change_in_db_fs = self.target_dBFS - a_chunk.dBFS
        return a_chunk.apply_gain(change_in_db_fs)

    def __split_audio_on_silence(self, audio_path):
        audio = AudioSegment.from_file(audio_path, self.audio_format)
        print("\n")
        print("*" * 10, "Splitting audio", "*" * 10)
        print(f"\n audio duration is {audio.duration_seconds} s")
        chunks = split_on_silence(audio, min_silence_len=self.min_silence_len, silence_thresh=self.silence_thresh,
                                  keep_silence=False)

        output_dir = os.path.join(self.output_path, os.path.splitext(os.path.basename(audio_path))[0])
        os.makedirs(output_dir)
        for i, chunk in enumerate(chunks):
            start_silence_chunk = AudioSegment.silent(duration=self.silence_padding // 2)
            end_silence_chunk = AudioSegment.silent(duration=self.silence_padding)

            # Add the padding chunk to beginning and end of the entire chunk.
            # audio_chunk = start_silence_chunk + chunk + end_silence_chunk
            audio_chunk = chunk

            # Normalize the entire chunk.
            normalized_chunk = self.__match_target_amplitude(audio_chunk)

            # Export the audio chunk with new bitrate.
            print(f"Exporting chunk{i + 1}.mp3")
            normalized_chunk.export(
                f"{output_dir}/chunk{i + 1}.mp3",
                bitrate="48k",  
                format="mp3"
            )
        self.__decrease_silence(output_dir)

    def __sequence_matcher(self, phrase, generated_text):
        return round(SequenceMatcher(None, phrase, generated_text).ratio(), 2)

    def __check_splitted_audio(self, audio_path):
        print("\n")
        print("*" * 10, "Validating splitted audios", "*" * 10)
        print("\n")
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        chunks_src = os.path.join(self.output_path, audio_name)
        validated_src = os.path.join(self.output_path, f"{audio_name}-validated")
        self.validated_srcs.append(validated_src)
        os.makedirs(validated_src)
        chunks = os.listdir(chunks_src)
        for chunk in chunks:
            full_file_name = os.path.join(chunks_src, chunk)
            if os.path.isfile(full_file_name):
                text = self.stt.whisper_func(full_file_name)
                phrases = pd.read_csv(os.path.join(self.input_path, "text", f"{audio_name}.csv"))
                for i in range(len(phrases)):
                    phrase = phrases.iloc[i]['text']
                    file_name = phrases.iloc[i]["file_name"]
                    ratio = self.__sequence_matcher(phrase, text)
                    if ratio > 0.90:
                        os.rename(full_file_name, os.path.join(validated_src, f'{file_name}.mp3'))
                        print(phrase, "====>", text, ratio)
        time.sleep(3)
        for chunk in chunks:
            full_file_name = os.path.join(chunks_src, chunk)
            if os.path.isfile(full_file_name):
                print("\n")
                print("*" * 10, f"This file have not splitted successfully. Please check it: ", "*" * 10)
                print(full_file_name, "\n")

    def split(self):
        self.__get_input_files()
        if len(self.audios_list) == 0:
            return print("*" * 10,
                         f"Please enter your audio file name using -a flag: -a /path_to_audio/{self.input_uid}.mp3",
                         "*" * 10)
        for audio in self.audios_list:
            self.__split_audio_on_silence(audio)
            self.__check_splitted_audio(audio)

    def upload_audios(self):
        url = "https://api.learnit.ir/v1/index.php/files"
        if self.env == "staging":
            url = "https://apilab.learnit.ir/v1/index.php/files"
        for validate_src in self.validated_srcs:
            chunks = os.listdir(validate_src)
            try:
                for chunk in chunks:
                    full_file_path = os.path.join(validate_src, chunk)
                    full_file_name = os.path.basename(full_file_path)
                    file_name = os.path.splitext(full_file_name)[0]

                    payload = {}
                    files = [
                        ('file', (f'{full_file_name}', open(f'{full_file_path}', 'rb'), 'audio/mpeg'))
                    ]
                    headers = {
                        'Authorization': f'Bearer {self.access_token}',
                        "Apikey": "PpAE(&9bskhHM8xC5W26t4GqDYIf@$eBSLN%Q*+v"
                    }

                    response = requests.request("POST", url, headers=headers, data=payload, files=files)
                    print(response.text, response.status_code)
                    key = f'{validate_src}'
                    if response.status_code == 200:
                        self.uploaded_audios[key] = self.uploaded_audios.get(key, []) + [
                            {"id": response.json()['data']['id'], "file_name": file_name}]
                        print(f"File {full_file_name} uploaded.")
            except:
                raise Exception(f"Uploading files failed with status code {response.status_code} please try again!")

    def upload_resources(self):
        url = "https://glossary.learnit.ir/glossary/resources"
        if self.env == 'staging':
            url = "https://glossarylab.learnit.ir/glossary/resources"
        for audio_path in self.uploaded_audios:
            text_name = os.path.basename(audio_path).split('-validated')[0]
            text_path = os.path.join(self.input_path, "text", text_name)
            resources = []

            df = pd.read_csv(f'{text_path}.csv')
            try:
                for uploaded_audio in self.uploaded_audios[audio_path]:
                    resources.append(
                        {
                            "text": df[df['file_name'] == uploaded_audio['file_name']]['raw_text'].array[0],
                            "file_id": uploaded_audio['id']
                        }
                    )
                body = {
                    "resources": resources,
                    "type": self.examples_type
                }
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    "Apikey": "PpAE(&9bskhHM8xC5W26t4GqDYIf@$eBSLN%Q*+v"
                }
                payload = json.dumps(body)
                response = requests.request("PUT", url, headers=headers, data=payload)
                print(response.text, response.status_code)
                if response.status_code == 200:
                    print("Resources uploaded to glossary service")
            except:
                raise Exception(
                    f"Uploading resources to glossary service failed with status code {response.status_code} please try again!")
