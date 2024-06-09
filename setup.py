import os

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

from global_variables import (
    BASE_MODEL_DIRECTORY,
    BASE_DATA_DIRECTORY,
    BASE_DATABASE_DIRECTORY,
    BASE_TEMP_DIRECTORY,
    DEFAULT_SPEECH_MODEL,
    DEFAULT_SUMMARY_MODEL,
    SPEECH_MODEL_PATH,
    SUMMARY_MODEL_PATH,
    BASE_DATA_UPLOADED_RECORDINGS_DIRECTORY,
    BASE_DATA_CONVERTED_RECORDINGS_DIRECTORY
)

def create_directories(*dirs):
    for each_dir in dirs:
        if not os.path.exists(each_dir):
            os.makedirs(each_dir, exist_ok=True)


create_directories(BASE_DATA_DIRECTORY, BASE_DATABASE_DIRECTORY, BASE_MODEL_DIRECTORY, BASE_TEMP_DIRECTORY, SPEECH_MODEL_PATH, SUMMARY_MODEL_PATH, BASE_DATA_UPLOADED_RECORDINGS_DIRECTORY, BASE_DATA_CONVERTED_RECORDINGS_DIRECTORY)


def download_speech_model():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        DEFAULT_SPEECH_MODEL, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(DEFAULT_SPEECH_MODEL)
    model.save_pretrained(SPEECH_MODEL_PATH)
    processor.save_pretrained(SPEECH_MODEL_PATH)


def download_summary_model():
    os.popen(f"huggingface-cli download '{DEFAULT_SUMMARY_MODEL[0]}' '{DEFAULT_SUMMARY_MODEL[1]}' --local-dir {SUMMARY_MODEL_PATH} --local-dir-use-symlinks False").read()

download_speech_model()
download_summary_model()
