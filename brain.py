from transformers import AutoModelForQuestionAnswering, AutoTokenizer, CamembertForQuestionAnswering, pipeline, AutoConfig
from qa_pipline import QAPipeline
qa_model = None
kmutt_context = None

# model_name = "airesearch/wangchanberta-base-wiki-20210520-spm-finetune-qa"
model_name = "deepset/roberta-large-squad2"

def init_brain():
    global qa_model, kmutt_context
    
    # 3. Create pipeline using the objects instead of the string name
    qa_model = QAPipeline(model_name)
    # qa_model = pipeline("question-answering", model=model_name)

def context_fibo():
    return ("""
    The Fibonacci sequence is a series of numbers where each number is the sum of the two preceding ones, usually starting with 0 and 1. 
    The sequence goes: 0, 1, 1, 2, 3, 5, 8, 13, 21, and so on. 
    It is named after the Italian mathematician Leonardo Fibonacci who introduced it to the Western world in his book "Liber Abaci" in 1202.
    """
)

def context_telesorting():
    return ("""
    Telesorting is a sorting algorithm that uses a divide-and-conquer approach to sort large datasets. 
    It works by recursively dividing the dataset into smaller subarrays, sorting each subarray independently, and then merging the sorted subarrays back together. 
    The algorithm is efficient for sorting large datasets and can be implemented in parallel to further improve performance.
    """
)   
def think(question,context):
    global qa_mode
    
    result = qa_model(question=question, context=context)
    return result['answer']

if __name__ == "__main__":
    init_brain()
    q = "What is 2B-KMUTT?"
    print(f"Answer: {think(q)}")