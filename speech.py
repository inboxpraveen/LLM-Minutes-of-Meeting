import torch
import os
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from faster_whisper import WhisperModel

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32


class OpenAI_Whisper:

    whisper_models = [
        "openai/whisper-large-v3",
        "openai/whisper-large-v2",
        "openai/whisper-large",
        "openai/whisper-medium.en",
        "openai/whisper-small.en",
        "openai/whisper-base.en",
        "openai/whisper-tiny.en"
    ]

    def __init__(self, model_name: str):
        if model_name in self.whisper_models:
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            model.to(device)

            processor = AutoProcessor.from_pretrained(model_name)
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,

                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                torch_dtype=torch_dtype,
                device=device,
                generate_kwargs={"language": "english", "task":"transcribe"}
            )
        else:
            raise f"No Such Whisper Model Exists. Please consider choosing from the following: {self.whisper_models}"

    def transcribe(self, audio_path: str):
        if os.path.exists(audio_path):
            try:
                result = self.pipeline(audio_path)
                return result["text"]
            except Exception as e:
                print(f"Something went wrong during audio transcription. The following error reported: {e}")
                return "ERROR"
        else:
            raise f"Audio file not located at: {audio_path}"


class Faster_Whisper:
    faster_whisper_models = [
        "large-v3",
        "large-v2",
        "large-v1",
        "medium.en",
        "small.en",
        "base.en",
        "tiny.en"
    ]
    def __init__(self, model_name):
        if model_name in self.faster_whisper_models:
            self.pipeline = WhisperModel(
                model_name,
                device=device
            )
            return self.pipeline
        else:
            raise f"No such Faste Whisper Model exists. Please choose from the following list: {self.faster_whisper_models}"
    
    def transcribe(self, audio_path):
        if os.path.exists(audio_path):
            try:
                segments, info = self.pipeline.transcribe(audio_path, word_timestamps=False)
                result = ""
                for segment in segments:
                    for word in segment.words:
                        result += f" {word.word}"
                return result
            except Exception as e:
                print(f"Something went wrong during audio transcription. The following error reported: {e}")
                return "ERROR"
        else:
            raise f"Audio file not located at: {audio_path}"

