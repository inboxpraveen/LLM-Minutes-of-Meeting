import os

DIRECTORY_NAME_MODEL = "models"
DIRECTORY_NAME_TEMP = "temp"
DIRECTORY_NAME_DATA = "data"
DIRECTORY_NAME_UPLOADED_RECORDING_FILES = "uploaded_recordings"
DIRECTORY_NAME_CONVERTED_RECORDING_FILES = "converted_audio_recordings"
DIRECTORY_NAME_DATABASE = "db"

ROOT_DIRECTORY = os.getcwd()

BASE_MODEL_DIRECTORY = os.path.join(ROOT_DIRECTORY, DIRECTORY_NAME_MODEL)
BASE_DATA_DIRECTORY = os.path.join(ROOT_DIRECTORY, DIRECTORY_NAME_DATA)
BASE_DATA_UPLOADED_RECORDINGS_DIRECTORY = os.path.join(BASE_DATA_DIRECTORY, DIRECTORY_NAME_UPLOADED_RECORDING_FILES)
BASE_DATA_CONVERTED_RECORDINGS_DIRECTORY = os.path.join(BASE_DATA_DIRECTORY, DIRECTORY_NAME_CONVERTED_RECORDING_FILES)
BASE_DATABASE_DIRECTORY = os.path.join(ROOT_DIRECTORY, DIRECTORY_NAME_DATABASE)
BASE_TEMP_DIRECTORY = os.path.join(ROOT_DIRECTORY, DIRECTORY_NAME_TEMP)


SPEECH_MODELS = (
    "distil-whisper/distil-large-v3",
    "distil-whisper/distil-large-v2",
    "distil-whisper/distil-medium.en",
    "distil-whisper/distil-small.en",
    "openai/whisper-large-v3",
    "openai/whisper-large-v2",
    "openai/whisper-large-v1",
    "openai/whisper-medium",
    "openai/whisper-small"
)

DEFAULT_SPEECH_MODEL = "openai/whisper-medium"
SPEECH_MODEL_PATH = os.path.join(BASE_MODEL_DIRECTORY, DEFAULT_SPEECH_MODEL)

SUMMARY_MODELS = (
    ("bartowski/Phi-3-medium-128k-instruct-GGUF","Phi-3-medium-128k-instruct-Q6_K.gguf"),
    ("bartowski/Phi-3-medium-128k-instruct-GGUF", "Phi-3-medium-128k-instruct-Q5_K_S.gguf"),
    ("QuantFactory/Phi-3-mini-128k-instruct-GGUF","Phi-3-mini-128k-instruct.Q8_0.gguf")
)

DEFAULT_SUMMARY_MODEL = ("QuantFactory/Phi-3-mini-128k-instruct-GGUF","Phi-3-mini-128k-instruct.Q8_0.gguf")
SUMMARY_MODEL_PATH = os.path.join(BASE_MODEL_DIRECTORY, DEFAULT_SUMMARY_MODEL[0])
