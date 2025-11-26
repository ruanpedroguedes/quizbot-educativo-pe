import re
import string
from unidecode import unidecode

class LightTextProcessor:
    def __init__(self):
        self.stop_words = set(['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 
                              'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
                              'nos', 'nas', 'por', 'para', 'com', 'sem', 'que',
                              'é', 'são', 'no', 'na', 'em'])
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza texto - VERSÃO MAIS PERMISSIVA"""
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
    
    def validate_answer(self, user_answer: str, correct_answers: list, threshold: float = 0.4) -> bool:
        """Valida se a resposta do usuário está correta - VERSÃO PARA TAGS"""
        print(f"🔍 VALIDAÇÃO COM TAGS:")
        print(f"   Usuário: '{user_answer}'")
        print(f"   Corretas: {correct_answers}")
        
        # CORREÇÃO: Se não há respostas válidas, aceita qualquer resposta
        if not correct_answers or all(not resp.strip() for resp in correct_answers):
            print("   ⚠️  ACEITO (sem respostas válidas no dataset)")
            return True
        
        user_clean = self.clean_text(user_answer)
        print(f"   Usuário limpo: '{user_clean}'")
        
        # Estratégia 1: Verificação exata (incluindo variações)
        for correct in correct_answers:
            if not correct.strip():
                continue
                
            correct_clean = self.clean_text(correct)
            print(f"   ➡️ Comparando: '{user_clean}' vs '{correct_clean}'")
            
            # Verificação exata
            if user_clean == correct_clean:
                print(f"   ✅ ACERTO EXATO")
                return True
            
            # Verificação parcial (um contém o outro)
            if user_clean in correct_clean or correct_clean in user_clean:
                print(f"   ✅ ACERTO PARCIAL (contém)")
                return True
        
        # Estratégia 2: Palavras-chave em comum (para nomes compostos)
        user_words = set(user_clean.split())
        for correct in correct_answers:
            if not correct.strip():
                continue
                
            correct_clean = self.clean_text(correct)
            correct_words = set(correct_clean.split())
            
            # Encontrar palavras significativas em comum
            common_words = user_words.intersection(correct_words)
            significant_common = [word for word in common_words if len(word) > 2]
            
            if significant_common:
                print(f"   ✅ ACERTO POR PALAVRAS: {significant_common}")
                return True
        
        # Estratégia 3: Similaridade tradicional
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
        """Calcula similaridade entre respostas"""
        if not user_answer or not correct_answer:
            return 0.0
        
        # Similaridade por Jaccard (palavras)
        user_set = set(user_answer.split())
        correct_set = set(correct_answer.split())
        
        if not user_set or not correct_set:
            return 0.0
        
        intersection = len(user_set.intersection(correct_set))
        union = len(user_set.union(correct_set))
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity