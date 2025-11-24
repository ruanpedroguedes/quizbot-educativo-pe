from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class QuestionProcessor:
    def __init__(self):
        # Modelo BERT em português mais leve - MESMA FUNCIONALIDADE
        self.model = SentenceTransformer('rufimelo/bert-base-portuguese-cased-nli')
        print("✅ QuestionProcessor inicializado com SentenceTransformer")
    
    def get_embeddings(self, texts):
        """
        Gera embeddings para textos - MESMA INTERFACE que o QuizSystem espera
        Retorna: numpy array de embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        # SentenceTransformer já retorna numpy array
        embeddings = self.model.encode(texts)
        return embeddings