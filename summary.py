import os
from llama_cpp import Llama
import torch

from global_variables import DEFAULT_SUMMARY_MODEL, SUMMARY_MODEL_PATH

def get_minutes_of_meeting(conversation):
    print(f"Loading Summary LLM")
    summary_llm = Llama(
        model_path=os.path.join(SUMMARY_MODEL_PATH, DEFAULT_SUMMARY_MODEL[1]),
        n_ctx=700,
        n_threads=8,
        n_gpu_layers=-1,
    )
    prompt = """<|user|>The conversation is given below:
======
{conversation}
======

You are provided with the above conversation without any speaker labels. Develop a comprehensive summary points using the the following Instructions given below.

### Instructions Begin ###
1. You will analyse the part of conversation and provide me comprehensive summary in bullet points.
2. You will stict to the facts of the conversations and ensure all points are clear and thorough.
3. If any part of the conversation is unclear, think step by step based on the context of the conversation, and then try to summarize it.
### Instructions End ###

Generate a comprehensive bullet point based summary using the above conversation and Instructions.<|end|>
<|assistant|>"""
    print(f"Loaded Summary LLM")
    
    print(f"Generating MoM")
    output = summary_llm(
        prompt.format(conversation=conversation),
        stop = ["<|end|>"],
        max_tokens = 100
    )
    del summary_llm
    torch.cuda.empty_cache()
    print(f"Finished Generating MoM")
    return output["choices"][0]["text"]

