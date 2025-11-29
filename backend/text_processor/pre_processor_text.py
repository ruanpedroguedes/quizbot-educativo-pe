import re
import string
from unidecode import unidecode
import spacy
import numpy as np

class LightTextProcessor:
    def __init__(self):
        self.stop_words = set(['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 
                              'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
                              'nos', 'nas', 'por', 'para', 'com', 'sem', 'que',
                              'é', 'são', 'no', 'na', 'em'])
        
        # Carrega o modelo spaCy em português (~40MB)
        try:
            self.nlp = spacy.load("pt_core_news_md")
            self.use_spacy = True
            print("✅ spaCy carregado com sucesso!")
        except OSError:
            print("❌ Modelo spaCy não encontrado. Usando fallback simples.")
            self.use_spacy = False
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza texto"""
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Remover acentos
        text = unidecode(text)
        
        # Remover pontuação mas manter espaços
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remover números
        text = re.sub(r'\d+', '', text)
        
        # Remover espaços extras
        text = ' '.join(text.split())
        
        return text
    
    def validate_answer(self, user_answer: str, correct_answers: list, threshold: float = 0.7) -> bool:
        """Valida resposta usando spaCy com word vectors"""
        print(f"🔍 VALIDAÇÃO:")
        print(f"   Usuário: '{user_answer}'")
        print(f"   Corretas: {correct_answers}")
        
        # CORREÇÃO: Se não há respostas válidas, aceita qualquer resposta
        if not correct_answers or all(not resp.strip() for resp in correct_answers):
            print("   ⚠️  ACEITO (sem respostas válidas no dataset)")
            return True
        
        # Se spaCy disponível, usa método inteligente
        if self.use_spacy:
            return self._validate_with_spacy(user_answer, correct_answers, threshold)
        else:
            # Fallback para método simples
            return self._validate_simple(user_answer, correct_answers, 0.4)
    
    def _validate_with_spacy(self, user_answer: str, correct_answers: list, threshold: float) -> bool:
        """Valida usando spaCy com word vectors"""
        print("   🧠 Usando spaCy com word vectors...")
        
        # Processar resposta do usuário
        user_doc = self.nlp(user_answer)
        
        best_similarity = 0
        for correct_answer in correct_answers:
            if not correct_answer.strip():
                continue
                
            # Processar resposta correta
            correct_doc = self.nlp(correct_answer)
            
            # Similaridade usando word vectors do spaCy
            similarity = user_doc.similarity(correct_doc)
            best_similarity = max(best_similarity, similarity)
            
            print(f"   ➡️ '{user_answer}' vs '{correct_answer}': {similarity:.3f}")
            
            if similarity >= threshold:
                print(f"   ✅ ACEITO (similaridade: {similarity:.3f})")
                return True
        
        print(f"   ❌ REJEITADO (melhor: {best_similarity:.3f}, threshold: {threshold})")
        return best_similarity >= threshold
    
    def _validate_simple(self, user_answer: str, correct_answers: list, threshold: float) -> bool:
        """Método simples de fallback"""
        print("   ⚡ Usando método simples (fallback)...")
        
        user_clean = self.clean_text(user_answer)
        
        # Estratégia 1: Verificação exata
        for correct in correct_answers:
            if not correct.strip():
                continue
                
            correct_clean = self.clean_text(correct)
            
            if user_clean == correct_clean:
                print(f"   ✅ ACERTO EXATO")
                return True
            
            if user_clean in correct_clean or correct_clean in user_clean:
                print(f"   ✅ ACERTO PARCIAL (contém)")
                return True
        
        # Estratégia 2: Similaridade Jaccard
        best_similarity = 0
        for correct in correct_answers:
            if not correct.strip():
                continue
                
            correct_clean = self.clean_text(correct)
            similarity = self.calculate_similarity(user_clean, correct_clean)
            best_similarity = max(best_similarity, similarity)
            
            if best_similarity >= threshold:
                print(f"   ✅ ACERTO POR SIMILARIDADE: {best_similarity:.2f}")
                return True
        
        print(f"   ❌ NÃO ACERTOU. Melhor similaridade: {best_similarity:.2f}")
        return False
    
    def calculate_similarity(self, user_answer: str, correct_answer: str) -> float:
        """Calcula similaridade Jaccard entre respostas (fallback)"""
        if not user_answer or not correct_answer:
            return 0.0
        
        user_set = set(user_answer.split())
        correct_set = set(correct_answer.split())
        
        if not user_set or not correct_set:
            return 0.0
        
        intersection = len(user_set.intersection(correct_set))
        union = len(user_set.union(correct_set))
        
        return intersection / union if union > 0 else 0
    
    def get_text_info(self, text: str):
        """Método útil para debug: mostra informações do texto processado"""
        if not self.use_spacy:
            return "spaCy não disponível"
        
        doc = self.nlp(text)
        info = {
            'text': text,
            'tokens': [token.text for token in doc],
            'vector_shape': doc.vector.shape if doc.vector is not None else None,
            'has_vectors': doc.has_vector
        }
        return info