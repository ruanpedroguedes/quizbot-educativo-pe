import uuid
from datetime import datetime

class UserGameState:
    def __init__(self, nome_usuario):
        self.nome_usuario = nome_usuario
        self.session_id = str(uuid.uuid4())
        self.pontuacao = 0
        self.questao_atual = None
        self.resposta_correta = None
        self.tentativas = 0
        self.historico = []
        self.questoes_respondidas = 0
        self.acertos = 0
        self.criado_em = datetime.now()
    
    def to_dict(self):
        return {
            'nome_usuario': self.nome_usuario,
            'pontuacao': self.pontuacao,
            'questoes_respondidas': self.questoes_respondidas,
            'acertos': self.acertos,
            'taxa_acerto': f"{(self.acertos/self.questoes_respondidas*100):.1f}%" if self.questoes_respondidas > 0 else "0%",
            'session_id': self.session_id
        }