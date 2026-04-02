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
    King Mongkut's University of Technology Thonburi (KMUTT) is a leading engineering and technology university in Thailand, known for innovation, research, and strong programs in science, engineering, and digital technology, with its main campus located in Thung Khru, Bangkok.
    to be KMUTT Camp is a preparatory and orientation program designed for high school students interested in studying at KMUTT, providing hands-on activities, workshops, and guidance to help participants explore engineering and technology fields while experiencing university life and building foundational skills needed to be future KMUTT students.
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