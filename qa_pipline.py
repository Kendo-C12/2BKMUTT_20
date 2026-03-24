import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering


class QAPipeline:
    def __init__(self, model_name: str):
        # use_fast=True is required for offset_mapping and sequence_ids()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        self.model.eval()

    def __call__(self, question: str, context: str,
                 top_k: int = 1,
                 max_answer_len: int = 100,
                 max_seq_len: int = 512) -> dict | list:

        # Step 1: Tokenize with offset mapping
        encoding = self.tokenizer(
            question,
            context,
            return_tensors="pt",
            truncation=True,
            max_length=max_seq_len,
            return_offsets_mapping=True,
        )

        offset_mapping = encoding.pop("offset_mapping")[0]   # shape: (seq_len, 2)

        # Step 2: Use sequence_ids() — works for ALL models including RoBERTa
        # sequence_ids() returns: None=special token, 0=question, 1=context
        sequence_ids = encoding.encodings[0].sequence_ids    # list of None | 0 | 1
        context_mask = [sid == 1 for sid in sequence_ids]

        # Step 3: Run model (no token_type_ids needed — AutoModel handles it)
        with torch.no_grad():
            outputs = self.model(**encoding)

        start_logits = outputs.start_logits[0]
        end_logits   = outputs.end_logits[0]
        seq_len      = len(sequence_ids)

        # Step 4: Score all valid (start, end) pairs within context only
        candidates = []
        for s in range(seq_len):
            if not context_mask[s]:
                continue
            for e in range(s, min(s + max_answer_len, seq_len)):
                if not context_mask[e]:
                    break
                score = (start_logits[s] + end_logits[e]).item()
                candidates.append((score, s, e))

        if not candidates:
            empty = {"score": 0.0, "start": 0, "end": 0, "answer": ""}
            return empty if top_k == 1 else [empty]

        candidates.sort(key=lambda x: x[0], reverse=True)

        # Step 5: Recover answer text using char offsets
        results = []
        for score, s, e in candidates[:top_k]:
            char_start = offset_mapping[s][0].item()
            char_end   = offset_mapping[e][1].item()
            answer     = context[char_start:char_end].strip()

            if not answer:
                continue

            results.append({
                "score":  round(score, 4),
                "start":  char_start,
                "end":    char_end,
                "answer": answer,
            })

        if not results:
            empty = {"score": 0.0, "start": 0, "end": 0, "answer": ""}
            return empty if top_k == 1 else [empty]

        return results[0] if top_k == 1 else results