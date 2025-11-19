import pandas as pd
import torch
from transformers import BertTokenizer, BertModel
import numpy as np

class QuestionProcessor:
    def __init__(self):
       self.model = BertModel.from_pretrained('neuralmind/bert-base-portuguese-cased')
       self.tokenizer = BertTokenizer.from_pretrained('neuralmind/bert-base-portuguese-cased') 
       self.model.eval()

    def preprocess_text(self, texto):
        if pd.isna(texto):
           return "" 

        return str(texto).strip()

    def get_embeddings(self, textos):
        embeddings = []
        
        for texto in textos:
            texto_processado = self.preprocess_text(texto)

            input = self.tokenizer(
                texto_processado,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512,
                return_attention_mask=True
            )

            return np.array(embeddings)
