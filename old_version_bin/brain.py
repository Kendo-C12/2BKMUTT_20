from transformers import AutoModelForQuestionAnswering, AutoTokenizer, CamembertForQuestionAnswering, pipeline, AutoConfig
from qa_pipline import QAPipeline
qa_model = None
kmutt_context = None

model_name = "airesearch/wangchanberta-base-wiki-20210520-spm-finetune-qa"
# model_name = "deepset/roberta-large-squad2"

def init_brain():
    global qa_model, kmutt_context
    
    # 1. Load context
    with open("context_thai.txt", "r", encoding="utf-8") as f:
        kmutt_context = f.read()

    # 3. Create pipeline using the objects instead of the string name
    qa_model = QAPipeline(model_name)

def think(question):
    global qa_model, kmutt_context
    
    result = qa_model(question=question, context=kmutt_context)
    return result['answer']

if __name__ == "__main__":
    init_brain()
    q = "What is KMUTT?"
    print(f"Answer: {think(q)}")