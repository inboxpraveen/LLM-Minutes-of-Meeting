import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from global_variables import SPEECH_MODEL_PATH


def get_speech_transcription(audio_path):
    
    runnning_device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        SPEECH_MODEL_PATH, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(runnning_device)

    processor = AutoProcessor.from_pretrained(SPEECH_MODEL_PATH)

    speech_pipeline = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=20,
        batch_size=8,
        torch_dtype=torch_dtype,
        device=runnning_device,
    )
    
    print(f"Transcribing...")
    result = speech_pipeline(audio_path, return_timestamps=False)
    print(f"Finished Transcribing...")
    print(f"{result}")
    del speech_pipeline, model, processor
    torch.cuda.empty_cache()
    
    return result['text']
