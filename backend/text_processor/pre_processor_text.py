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

            inputs = self.tokenizer(
                texto_processado,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512,
                return_attention_mask=True
            )

            # Gera os embeddings sem calculo de gradiente
            with torch.no_grad():
                outputs = self.model(**inputs)

                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.append(embedding[0])

            return np.array(embeddings)
