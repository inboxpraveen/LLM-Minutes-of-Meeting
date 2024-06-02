import os
from llama_cpp import Llama

from global_variables import DEFAULT_SUMMARY_MODEL, SUMMARY_MODEL_PATH

class SummaryModel:

    def __init__(self) -> None:
        print(f"Loading Summary LLM")
        self.summary_llm = Llama(
            model_path=os.path.join(SUMMARY_MODEL_PATH, DEFAULT_SUMMARY_MODEL[1]),
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=-1,
        )
        self.prompt = """<|user|>
You are provided with a conversation. Develop a comprehensive Minutes of Meeting consider the following Instructions.
Instructions:
Discussion Points: Detail the topics discussed, including any debates or alternate viewpoints.
Decisions Made: Record all decisions, including who made them and the rationale.
Action Items: Specify tasks assigned, responsible individuals, and deadlines.
Data & Insights: Summarize any data presented or insights shared that influenced the meeting's course.
Follow-Up: Note any agreed-upon follow-up meetings or checkpoints.

===
Conversation:
{conversation}
===<|end|>
<|assistant|>"""
        print(f"Loaded Summary LLM")

    def get_mom(self, conversation):
        print(f"Generating MoM")
        output = self.summary_llm(
            self.prompt.format(conversation=conversation),
            stop = ["<|end|>"],
            max_tokens = 512
        )
        print(f"Finished Generating MoM")
        return output["choices"][0]["text"]
    
    def clear_memory(self):
        self.summary_llm = None
        del self.summary_llm

