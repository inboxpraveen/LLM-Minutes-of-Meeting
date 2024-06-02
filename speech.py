import torch
import os
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from global_variables import SPEECH_MODEL_PATH

class SpeechRecognition:
    
    def __init__(self):
        
        assert os.path.exists(SPEECH_MODEL_PATH), "Speech Model is not loaded. Please run `setup.py` before running the main application."
        print(f"Loading Speech Model")
        self.runnning_device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.speech_pipeline = self.load_distil_or_whisper_speech_model()
        print(f"Speech Model Loaded")
    
    def load_distil_or_whisper_speech_model(self):
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            SPEECH_MODEL_PATH, torch_dtype=self.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(self.runnning_device)

        processor = AutoProcessor.from_pretrained(SPEECH_MODEL_PATH)

        return pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=15,
            batch_size=1,
            torch_dtype=self.torch_dtype,
            device=self.runnning_device,
        )
    
    def transcribe(self, audio_path):
        print(f"Transcribing...")
        result = self.speech_pipeline(audio_path)
        print(f"Finished Transcribing...")
        return result['text']
    
    def clear_memory(self):
        self.speech_pipeline = None
        del self.speech_pipeline
