from typing import Dict, Optional, List
import json
import random

class GameState:
    def __init__(self):
        self.players = {}
        self.dataset = self.load_dataset()
        self.attempts_tracker = {}  # Rastrear tentativas por usuário
    
    def initialize_player(self, user_id: str):
        """Inicializa estado do jogador"""
        self.players[user_id] = {
            'score': 0,
            'current_stage': 0,
            'current_place': None,
            'answered_text': False,
            'attempts': 0
        }
        self.attempts_tracker[user_id] = 0
    
    def load_dataset(self) -> list:
        """Carrega o dataset com a estrutura real"""
        try:
            with open('datasets/dataset_pernambuco_25_turistas.json', 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            print(f"✅ Dataset carregado: {len(dataset)} itens")
            
            # DEBUG: Mostrar estrutura do primeiro item
            if dataset:
                first_item = dataset[0]
                print(f"🔍 Estrutura do primeiro item: {list(first_item.keys())}")
                print(f"🔍 Exemplo: Pergunta: '{first_item.get('pergunta')}'")
                print(f"🔍 Exemplo: Tags: {first_item.get('tags')}")
            
            return dataset
            
        except Exception as e:
            print(f"❌ Erro ao carregar dataset: {e}")
            return []

    def get_random_place(self, user_id: str) -> Dict:
        """Seleciona um lugar aleatório do dataset"""
        if not self.dataset:
            raise ValueError("Dataset não carregado corretamente")
        
        place = random.choice(self.dataset)
        
        # DEBUG: Mostrar dados do lugar selecionado
        print(f"🎯 LUGAR SELECIONADO (ESTRUTURA REAL):")
        print(f"   ID: {place.get('id')}")
        print(f"   Pergunta: {place.get('pergunta')}")
        print(f"   Tags: {place.get('tags', [])}")
        print(f"   Contexto: {place.get('contexto', '')[:50]}...")
        
        self.players[user_id]['current_place'] = place
        self.players[user_id]['current_stage'] = 0
        self.players[user_id]['answered_text'] = False
        self.players[user_id]['attempts'] = 0
        
        return place

    def validate_text_answer(self, user_id: str, user_answer: str, text_processor) -> Dict:
        """Valida resposta de texto - VERSÃO PARA ESTRUTURA REAL"""
        if user_id not in self.players:
            return {'correct': False, 'hint': None, 'attempts': 0}
        
        place = self.players[user_id]['current_place']
        if not place:
            return {'correct': False, 'hint': "💡 Dica: Erro no jogo. Reinicie.", 'attempts': 0}
        
        # DEBUG Detalhado com estrutura real
        print(f"🔍 VALIDAÇÃO (ESTRUTURA REAL):")
        print(f"   ID: {place.get('id')}")
        print(f"   Pergunta: {place.get('pergunta')}")
        print(f"   Tags: {place.get('tags', [])}")
        print(f"   Resposta usuário: '{user_answer}'")
        
        # Incrementar tentativas
        self.players[user_id]['attempts'] += 1
        self.attempts_tracker[user_id] = self.players[user_id]['attempts']
        
        # CORREÇÃO: Extrair respostas corretas das TAGS
        tags = place.get('tags', [])
        
        # Filtrar tags genéricas e manter apenas as específicas do lugar
        generic_words = {'turismo', 'história', 'cultura', 'natureza', 'praia', 'museu', 
                        'arte', 'festa', 'gastronomia', 'visita', 'passeio', 'aventura',
                        'litoral', 'sertão', 'serra', 'inverno', 'tradição', 'ecoturismo'}
        
        correct_answers = [tag for tag in tags if tag not in generic_words]
        
        # Se não encontrou tags específicas, extrair da pergunta
        if not correct_answers:
            pergunta = place.get('pergunta', '')
            # Extrair possíveis nomes da pergunta
            if "Marco Zero" in pergunta:
                correct_answers = ["Marco Zero", "Recife Antigo"]
            elif "Olinda" in pergunta:
                correct_answers = ["Olinda"]
            elif "Porto de Galinhas" in pergunta:
                correct_answers = ["Porto de Galinhas", "Ipojuca"]
            elif "Fernando de Noronha" in pergunta:
                correct_answers = ["Fernando de Noronha", "Noronha"]
            # Adicione mais casos conforme necessário
        
        print(f"   Respostas extraídas: {correct_answers}")
        
        is_correct = text_processor.validate_answer(user_answer, correct_answers)
        
        # Gerar dica baseada no número de tentativas
        hint = self._generate_hint(user_id, place)
        
        if is_correct:
            self.players[user_id]['score'] += 1
            self.players[user_id]['current_stage'] = 1
            self.players[user_id]['answered_text'] = True
            self.players[user_id]['attempts'] = 0
            
            return {
                'correct': True,
                'hint': None,
                'attempts': self.attempts_tracker[user_id],
                'message': "🎉 Resposta correta!"
            }
        else:
            return {
                'correct': False,
                'hint': hint,
                'attempts': self.attempts_tracker[user_id],
                'message': f"❌ Resposta incorreta. {hint}"
            }

    def _generate_hint(self, user_id: str, place: Dict) -> str:
        """Gera dicas baseadas na estrutura real do dataset"""
        attempts = self.players[user_id]['attempts']
        tags = place.get('tags', [])
        contexto = place.get('contexto', '')
        pergunta = place.get('pergunta', '')
        
        # Extrair o nome principal das tags ou da pergunta
        main_tags = [tag for tag in tags if tag not in 
                    {'turismo', 'história', 'cultura', 'natureza', 'praia', 'visita'}]
        
        main_place = main_tags[0] if main_tags else "este lugar"
        
        hints = [
            f"💡 Dica: {contexto.split('.')[0] if contexto else 'É um ponto turístico de Pernambuco'}",
            f"💡 Dica: {self._get_region_hint_from_context(contexto)}",
            f"💡 Dica: Começa com '{main_place[0].upper()}'" if main_tags else "💡 Dica: Pense em destinos famosos de PE",
            f"💡 Dica: É {main_place}",
            f"💡 Dica: O lugar é {main_place}"
        ]
        
        hint_index = min(attempts - 1, len(hints) - 1)
        return hints[hint_index] if hint_index >= 0 else hints[0]

    def _get_region_hint_from_context(self, contexto: str) -> str:
        """Gera dica sobre a região baseada no contexto"""
        contexto_lower = contexto.lower()
        
        if any(word in contexto_lower for word in ['praia', 'litoral', 'mar', 'costa', 'praias']):
            return "Fica no litoral de Pernambuco"
        elif any(word in contexto_lower for word in ['serra', 'montanha', 'sertão', 'interior', 'frio']):
            return "Fica no interior de Pernambuco"
        elif any(word in contexto_lower for word in ['recife', 'metropolitana']):
            return "Fica na região metropolitana do Recife"
        else:
            return "É um destino turístico de Pernambuco"
    
    def get_player_score(self, user_id: str) -> int:
        """Retorna pontuação do jogador"""
        return self.players.get(user_id, {}).get('score', 0)
    
    def get_current_stage(self, user_id: str) -> int:
        """Retorna estágio atual do jogador"""
        return self.players.get(user_id, {}).get('current_stage', 0)
    
    def get_attempts(self, user_id: str) -> int:
        """Retorna número de tentativas do usuário"""
        return self.players.get(user_id, {}).get('attempts', 0)
    
    async def validate_image_answer(self, user_id: str, image_bytes: bytes, image_processor) -> bool:
        """Valida imagem enviada pelo usuário"""
        if user_id not in self.players or not self.players[user_id]['answered_text']:
            print(f"❌ Usuário {user_id} não autorizado para envio de imagem")
            return False
        
        place = self.players[user_id]['current_place']
        if not place:
            print(f"❌ Lugar atual não definido para {user_id}")
            return False
        
        print(f"🎯 Validando imagem para: {place.get('id')} - {place.get('tags', [])[0] if place.get('tags') else 'Unknown'}")
        
        # Validação da imagem
        is_correct = await image_processor.validate_user_image(image_bytes, place)
        
        if is_correct:
            self.players[user_id]['score'] += 1
            print(f"✅ Imagem aceita! Pontuação: {self.players[user_id]['score']}")
            
            # SÓ FAZ RESET SE ACERTOU
            self.players[user_id]['current_stage'] = 0
            self.players[user_id]['answered_text'] = False
            self.players[user_id]['current_place'] = None
            self.players[user_id]['attempts'] = 0
        else:
            print(f"❌ Imagem rejeitada! Pontuação mantém: {self.players[user_id]['score']}")
            # NÃO FAZ RESET SE ERROU - permite nova tentativa!
            # Mantém o estado atual para o usuário tentar novamente
        
        return is_correct