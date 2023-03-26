import os
import shutil
import requests
import pandas as pd
from uuid import uuid4
from argparse import ArgumentParser
from splitter import Splitter
import warnings
warnings.filterwarnings('ignore')

parser = ArgumentParser()
parser.add_argument("-at", "--access_token", dest="access_token",
                    help="access token to get examples from glossary service", required=True)
parser.add_argument("-src", "--source_directory", dest="source_directory",
                    help="""source directory must contain a text and audio sub directory and 
                            the text file name must be the same as audio file name.""",
                    default=None)
parser.add_argument("-a", "--audio", dest="audio",
                    help="audio file name with the same name of the text file")
parser.add_argument("-t", "--type", dest="type",
                    help="enter type examples or definitions", required=True)

parser.add_argument("-env", "--environment", dest="environment",
                    help="enter environment staging or production", required=True)
parser.add_argument("-m", "--method", dest="method",
                    help="enter split if you just want to split audios", default=None)

args = parser.parse_args()
source_dir = args.source_directory
access_token = args.access_token
audio_file = args.audio
example_type = args.type
env = args.environment
method = args.method


def make_input_folders():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_uid = str(uuid4())
    parent_path = f'{dir_path}/../input/{dir_uid}'
    os.makedirs(os.path.join(parent_path, "audio"))
    os.makedirs(os.path.join(parent_path, "text"))
    return parent_path


def generate_file_name():
    return str(uuid4())


def copy_all_files(src, dist):
    if os.path.isdir(src):
        files = os.listdir(src)
        for file in files:
            file_full_name = os.path.join(src, file)
            if os.path.isfile(file_full_name):
                shutil.copy(file_full_name, dist)


def get_data():
    if access_token is None:
        raise Exception("Please enter access token using -at <your access_token>")
    dist_parent = make_input_folders()
    input_uid = dist_parent.split("/")[-1]
    if source_dir is None:
        get_text_form_api(dist_parent, access_token)
        return input_uid
    read_data_from_disk(source_dir, dist_parent)
    return input_uid


def get_text_form_api(dist_parent, token):
    input_uid = os.path.basename(dist_parent)
    data = get_examples_from_glossary(token)
    if data['raw_texts'] is None:
        print("No data found")
        return
    df = pd.DataFrame({"text": data['raw_texts'], "file_name": "", "raw_text": data['texts']})
    df['file_name'] = df['text'].apply(lambda x: str(uuid4()))
    output_dir = f'{dist_parent}/text/{input_uid}.csv'
    df.to_csv(output_dir)
    print(f"\nexamples file saved at {output_dir}")


def get_examples_from_glossary(token):
    url = "https://glossary.learnit.ir/glossary/resources"
    if env == 'staging':
        url = "https://glossarylab.learnit.ir/glossary/resources"
    print("\n")
    print("*" * 10, "getting examples fom glossary service", "*" * 10)
    res = requests.get(f"{url}?type={example_type}",
                       headers={"Authorization": f"Bearer {token}",
                                "Apikey": "PpAE(&9bskhHM8xC5W26t4GqDYIf@$eBSLN%Q*+v"})
    if res.status_code == 200:
        return res.json()['data']
    raise Exception(f"\ngetting examples from glossary service failed with status code {res.status_code} ! try again.")


def read_data_from_disk(src_dir, dist_dir):
    audio_src = f'{src_dir}/audio'
    text_src = f'{src_dir}/text'
    if not (os.path.isdir(audio_src) and os.path.isdir(text_src)):
        raise Exception("your source directory must contain a text and an audio sub directory")
    copy_all_files(audio_src, f'{dist_dir}/audio')
    copy_all_files(text_src, f'{dist_dir}/text')


def get_audio_data(audio_path):
    input_uid = os.path.splitext(os.path.basename(audio_path))[0]
    dist = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "input", input_uid, "audio")
    shutil.copy(audio_path, dist)
    return input_uid


def main():
    if env not in ["staging", "production"]:
        raise Exception("env value must be one of staging or production")
    if audio_file is not None:
        input_uid = get_audio_data(audio_file)
    else:
        input_uid = get_data()
    splitter = Splitter(env=env, examples_type=example_type, access_token=access_token, input_uid=input_uid,
                        audio_format="mp3",
                        target_db_fs=-20)

    if method == 'split':
        splitter.split()
        return

    splitter.split()
    splitter.upload_audios()
    splitter.upload_resources()


main()
