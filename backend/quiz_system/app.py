import random
from typing import Dict, Optional
from .game_state import GameState
from preprocessing.pre_processor_img import EfficientImageProcessor  # ✅ Atualizado
from text_processor.pre_processor_text import LightTextProcessor     # ✅ Já atualizado

class QuizSystem:
    def __init__(self):
        self.game_state = GameState()
        self.image_processor = EfficientImageProcessor()  # ✅ Nova classe
        self.text_processor = LightTextProcessor()        # ✅ Já atualizada
    
    def start_quiz(self, user_id: str) -> Dict:
        """Inicia um novo quiz para o usuário"""
        self.game_state.initialize_player(user_id)
        place = self.game_state.get_random_place(user_id)
        
        # Extrair informações da estrutura real
        tags = place.get('tags', [])
        main_tags = [tag for tag in tags if tag not in 
                    {'turismo', 'história', 'cultura', 'natureza', 'praia', 'visita'}]
        
        place_name = main_tags[0] if main_tags else "Local de Pernambuco"
        
        return {
            "success": True,
            "user_id": user_id,
            "place_data": {
                "nome": place_name,
                "imagem": place.get('imagem', [])[0] if place.get('imagem') else "",
                "pergunta": "Que lugar é este?",  # Pergunta fixa para o quiz
                "contexto": place.get('contexto', '')[:100] + "..."
            },
            "message": "🎮 Quiz iniciado! Adivinhe o lugar na imagem."
        }
    
    async def process_text_answer(self, user_id: str, user_answer: str) -> Dict:
        """Processa a resposta em texto do usuário"""
        try:
            validation_result = self.game_state.validate_text_answer(
                user_id, user_answer, self.text_processor
            )
            
            if validation_result['correct']:
                return {
                    "success": True,
                    "correct": True,
                    "message": "🎉 Parabéns! Você acertou! Agora envie uma foto deste local para ganhar mais pontos.",
                    "score": self.game_state.get_player_score(user_id),
                    "attempts": validation_result['attempts'],
                    "hint": None,
                    "next_action": "upload_image"
                }
            else:
                return {
                    "success": True,
                    "correct": False,
                    "message": f"❌ Resposta incorreta. {validation_result['hint']}",
                    "score": self.game_state.get_player_score(user_id),
                    "attempts": validation_result['attempts'],
                    "hint": validation_result['hint'],
                    "next_action": "retry_text"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar resposta: {str(e)}"
            }
    
    async def process_image_upload(self, user_id: str, image_bytes: bytes) -> Dict:
        """Processa a imagem enviada pelo usuário"""
        try:
            is_correct = await self.game_state.validate_image_answer(
                user_id, image_bytes, self.image_processor
            )
            
            if is_correct:
                final_score = self.game_state.get_player_score(user_id)
                return {
                    "success": True,
                    "correct": True,
                    "message": "📸 Excelente! Foto correta! Você completou esta rodada.",
                    "score": final_score,
                    "points_earned": 1,
                    "next_action": "quiz_completed"
                }
            else:
                # ✅ Mensagem mais clara para tentar novamente
                return {
                    "success": True,
                    "correct": False,
                    "message": "📷 Esta foto não parece ser do local correto. Tente enviar outra foto!",
                    "score": self.game_state.get_player_score(user_id),
                    "next_action": "retry_image"  # ✅ Permite retry
                }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar imagem: {str(e)}"
            }
    
    def get_user_progress(self, user_id: str) -> Dict:
        """Retorna o progresso atual do usuário"""
        try:
            stage = self.game_state.get_current_stage(user_id)
            score = self.game_state.get_player_score(user_id)
            attempts = self.game_state.get_attempts(user_id)
            current_place = self.game_state.players.get(user_id, {}).get('current_place')
            
            stage_descriptions = {
                0: "aguardando_resposta_texto",
                1: "aguardando_upload_imagem"
            }
            
            return {
                "success": True,
                "user_id": user_id,
                "score": score,
                "attempts": attempts,
                "current_stage": stage_descriptions.get(stage, "unknown"),
                "current_place": current_place.get('nome') if current_place else None,
                "has_answered_text": self.game_state.players.get(user_id, {}).get('answered_text', False)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao buscar progresso: {str(e)}"
            }
    
    def get_leaderboard(self) -> Dict:
        """Retorna ranking de jogadores"""
        try:
            players = self.game_state.players
            leaderboard = sorted(
                [(user_id, data['score']) for user_id, data in players.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10
            
            return {
                "success": True,
                "leaderboard": [
                    {"user_id": user_id, "score": score} 
                    for user_id, score in leaderboard
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar leaderboard: {str(e)}"
            }
    
    def skip_question(self, user_id: str) -> Dict:
        """Pula a pergunta atual e revela a resposta"""
        try:
            current_place = self.game_state.players.get(user_id, {}).get('current_place')
            if current_place:
                place_name = current_place.get('nome', 'Desconhecido')
                
                # Reset para próxima pergunta
                self.game_state.players[user_id]['current_stage'] = 0
                self.game_state.players[user_id]['answered_text'] = False
                self.game_state.players[user_id]['current_place'] = None
                self.game_state.players[user_id]['attempts'] = 0
                
                return {
                    "success": True,
                    "message": f"🔁 Pergunta pulada! A resposta era: {place_name}",
                    "correct_answer": place_name,
                    "next_action": "new_question"
                }
            else:
                return {
                    "success": False,
                    "error": "Nenhuma pergunta ativa para pular"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao pular pergunta: {str(e)}"
            }
    
    def get_system_info(self) -> Dict:
        """Retorna informações sobre o sistema"""
        try:
            return {
                "success": True,
                "system_info": {
                    "image_processor": self.image_processor.get_model_info(),
                    "text_processor": "spaCy com fallback" if self.text_processor.use_spacy else "método simples",
                    "total_players": len(self.game_state.players),
                    "dataset_size": len(self.game_state.dataset)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao obter informações do sistema: {str(e)}"
            }