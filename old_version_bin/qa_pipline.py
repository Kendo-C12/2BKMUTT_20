import torch
from transformers import CamembertForQuestionAnswering, AutoTokenizer, AutoModelForQuestionAnswering

class QAPipeline:
    def __init__(self, model_name: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        self.model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        self.model.eval()

    def __call__(self, question: str, context: str,
                 top_k: int = 1,
                 max_answer_len: int = 100,
                 max_seq_len: int = 512) -> dict | list:

        # Step 1: Tokenize (official HF docs approach)
        inputs = self.tokenizer(
            question,
            context,
            return_tensors="pt",
            truncation=True,
            max_length=max_seq_len
        )

        # Step 2: Run model
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Step 3: Get start/end positions (official HF docs approach)
        start_logits = outputs.start_logits[0]
        end_logits   = outputs.end_logits[0]
        input_ids    = inputs["input_ids"][0]
        seq_len      = len(input_ids)

        # Step 4: Score all valid (start, end) pairs
        candidates = []
        for s in range(seq_len):
            for e in range(s, min(s + max_answer_len, seq_len)):
                score = (start_logits[s] + end_logits[e]).item()
                candidates.append((score, s, e))

        candidates.sort(key=lambda x: x[0], reverse=True)

        # Step 5: Decode tokens → text (official HF docs approach)
        results = []
        for score, s, e in candidates[:top_k]:
            answer_tokens = input_ids[s : e + 1]                        # ← from official docs
            answer = self.tokenizer.decode(answer_tokens,               # ← from official docs
                                           skip_special_tokens=True)

            results.append({
                "score": round(score, 4),
                "start": s,
                "end":   e,
                "answer": answer
            })

        return results[0] if top_k == 1 else results
