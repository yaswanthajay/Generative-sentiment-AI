from llama_cpp import Llama
from config import settings

llm = Llama(
    model_path="model.gguf",
    n_ctx=2048,
    n_threads=8,
    n_gpu_layers=40,
    verbose=False
)

def ask_llama(prompt):
    output = llm(prompt, max_tokens=512, stop=["</s>"])
    return output['choices'][0]['text'].strip()
