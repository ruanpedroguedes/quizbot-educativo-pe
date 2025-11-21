import uuid
from datetime import datetime
import json
from text_processor.perguntas_respostas import QuestionProcessor
from quiz_system.game_state import UserGameState
from sklearn.metrics.pairwise import cosine_similarity
import random

class QuizSystem:
    def __init__(self):
        self.processor = QuestionProcessor()
        self.df = None
        self.question_embeddings = None
        self.locais_embeddings = None
        self.users_sessions = {}  # {nome_usuario: UserGameState}
        
    def treinamento(self, df):
        self.df = df.copy()
        
        print("🔄 Pré-computando embeddings...")
        
        # Embeddings para as perguntas
        combined_texts = [
            f"{pergunta} [SEP] {contexto}" for pergunta, contexto in zip(df['pergunta'], df['contexto'])
        ]
        self.question_embeddings = self.processor.get_embeddings(combined_texts)
        
        # Embeddings para validação de respostas
        nomes_locais = self._extrair_nomes_locais(df)
        self.locais_embeddings = self.processor.get_embeddings(nomes_locais)
        
        print(f"✅ Sistema treinado com {len(df)} locais!")
    
    def _extrair_nomes_locais(self, df):
        # Extrai os nomes principais dos locais
        nomes = []
        for contexto in df['contexto']:
            # Tenta extrair o nome do local de forma inteligente
            nome = contexto.split('.')[0]
            nome = nome.split(' é ')[0]
            nome = nome.split(' fica ')[0]
            nome = nome.split(' localizado ')[0]
            nomes.append(nome.strip())
        return nomes
    
    def criar_ou_recuperar_sessao(self, nome_usuario):
        # Cria nova sessão ou recupera existente pelo nome
        if nome_usuario in self.users_sessions:
            # Retorna sessão existente
            return self.users_sessions[nome_usuario].session_id
        else:
            # Cria nova sessão
            session = UserGameState(nome_usuario)
            self.users_sessions[nome_usuario] = session
            print(f"🎮 Nova sessão criada para: {nome_usuario}")
            return session.session_id
    
    def get_estatisticas_usuario(self, nome_usuario):
        # Retorna estatísticas do usuário
        if nome_usuario not in self.users_sessions:
            return None
        return self.users_sessions[nome_usuario].to_dict()
    
    def nova_questao(self, nome_usuario, tema=None):
        # Gera uma nova questão para o usuário
        if nome_usuario not in self.users_sessions:
            return {'erro': 'Usuário não encontrado. Crie uma sessão primeiro.'}
        
        session = self.users_sessions[nome_usuario]
        
        # Escolhe um local aleatório (pode filtrar por tema depois)
        idx = random.randint(0, len(self.df) - 1)
        local = self.df.iloc[idx]
        
        # Prepara a questão
        session.questao_atual = {
            'id': idx,
            'pergunta': local['pergunta'],
            'imagem': local.get('imagem', ''),
            'dica': self._gerar_dica_inteligente(local),
            'tags': local.get('tags', []),
            'dificuldade': self._calcular_dificuldade(local)
        }
        session.resposta_correta = local['contexto']
        session.tentativas = 0
        
        # Embedding para validação rápida
        resposta_embedding = self.processor.get_embeddings([local['contexto']])
        session.resposta_embedding = resposta_embedding[0]
        
        return {
            'questao': session.questao_atual,
            'session_id': session.session_id
        }
    
    def _calcular_dificuldade(self, local):
        # Calcula dificuldade baseada no contexto
        contexto = local['contexto']
        palavras = len(contexto.split())
        
        if palavras < 10:
            return "Fácil"
        elif palavras < 20:
            return "Médio"
        else:
            return "Difícil"
    
    def _gerar_dica_inteligente(self, local):
        # Gera dicas usando análise do contexto
        contexto = local['contexto']
        tags = local.get('tags', [])
        
        dicas = []
        
        # Dica baseada em tags
        if tags:
            dicas.append(f"🏷️ Tags: {', '.join(tags[:3])}")
        
        # Dica baseada no tipo de local
        if any(word in contexto.lower() for word in ['praia', 'mar', 'litoral']):
            dicas.append("🌊 É uma área litorânea")
        elif any(word in contexto.lower() for word in ['museu', 'histórico', 'patrimônio']):
            dicas.append("🏛️ Local histórico/cultural")
        elif any(word in contexto.lower() for word in ['parque', 'natureza', 'verde']):
            dicas.append("🌳 Área natural/parque")
        
        # Dica do nome
        nome = self._extrair_nome_do_contexto(contexto)
        if nome and len(nome.split()) > 1:
            dicas.append(f"📝 Nome tem {len(nome.split())} palavras")
        elif nome:
            dicas.append(f"📝 Começa com '{nome[0].upper()}'")
        
        return random.choice(dicas) if dicas else "💡 Ponto turístico famoso de Pernambuco"
    
    def _extrair_nome_do_contexto(self, contexto):
        # Extrai o nome do local do contexto
        # Remove descrições comuns
        descricoes = ['é um', 'é uma', 'fica', 'localizado', 'situado', 'conhecido']
        nome = contexto.split('.')[0]
        
        for desc in descricoes:
            if desc in nome:
                nome = nome.split(desc)[0]
        
        return nome.strip()
    
    def validar_resposta(self, nome_usuario, resposta_usuario):
        # Valida a resposta do usuário usando Deep Learning
        if nome_usuario not in self.users_sessions:
            return {'valido': False, 'erro': 'Usuário não encontrado'}
        
        session = self.users_sessions[nome_usuario]
        
        if not session.questao_atual:
            return {'valido': False, 'erro': 'Nenhuma questão ativa'}
        
        session.tentativas += 1
        session.questoes_respondidas += 1
        
        # Calcula similaridade com Deep Learning
        resposta_embedding = self.processor.get_embeddings([resposta_usuario])[0]
        
        similaridade_correta = cosine_similarity(
            [resposta_embedding], 
            [session.resposta_embedding]
        )[0][0]
        
        # Validação inteligente com threshold adaptável
        threshold = 0.72  # Pode ajustar baseado na dificuldade
        
        if similaridade_correta > threshold:
            # Acertou!
            pontos = self._calcular_pontos(similaridade_correta, session.tentativas)
            session.pontuacao += pontos
            session.acertos += 1
            
            session.historico.append({
                'questao': session.questao_atual['pergunta'],
                'resposta_usuario': resposta_usuario,
                'resposta_correta': session.resposta_correta,
                'tentativas': session.tentativas,
                'similaridade': float(similaridade_correta),
                'pontos_ganhos': pontos,
                'timestamp': datetime.now().isoformat()
            })
            
            # Prepara próxima questão
            proxima_questao = self.nova_questao(nome_usuario)
            
            return {
                'valido': True,
                'acertou': True,
                'pontuacao': session.pontuacao,
                'pontos_ganhos': pontos,
                'resposta_correta': session.resposta_correta,
                'tentativas': session.tentativas,
                'similaridade': float(similaridade_correta),
                'feedback': self._gerar_feedback_positivo(similaridade_correta),
                'proxima_questao': proxima_questao.get('questao') if not proxima_questao.get('erro') else None
            }
        
        else:
            # Não acertou
            return {
                'valido': True,
                'acertou': False,
                'feedback': self._gerar_feedback_negativo(similaridade_correta, session.tentativas),
                'tentativas': session.tentativas,
                'similaridade': float(similaridade_correta),
                'dica_extra': session.questao_atual['dica'] if session.tentativas >= 2 else None
            }
    
    def _calcular_pontos(self, similaridade, tentativas):
        # Calcula pontos baseados na qualidade da resposta e tentativas
        base_points = 100
        similarity_bonus = int(similaridade * 50)  # Até 50 pontos extra por precisão
        speed_bonus = max(0, 50 - (tentativas * 20))  # Bonus por menos tentativas
        
        return base_points + similarity_bonus + speed_bonus
    
    def _gerar_feedback_positivo(self, similaridade):
        if similaridade > 0.9:
            return "🎉 Resposta perfeita! Você conhece bem!"
        elif similaridade > 0.8:
            return "✅ Excelente! Quase perfeito!"
        elif similaridade > 0.75:
            return "👍 Muito bom! Acertou em cheio!"
        else:
            return "👏 Acertou! Mas pode ser mais específico..."
    
    def _gerar_feedback_negativo(self, similaridade, tentativas):
        if tentativas == 1:
            return "❌ Não é isso... Tente novamente!"
        elif tentativas == 2:
            return "❌ Ainda não... Pense nas características do local!"
        else:
            return "❌ Vamos tentar de outra forma... Que tal desistir e ver a resposta?"
    
    def desistir(self, nome_usuario):
        # Revela a resposta e gera nova questão
        if nome_usuario not in self.users_sessions:
            return {'erro': 'Usuário não encontrado'}
        
        session = self.users_sessions[nome_usuario]
        
        if not session.questao_atual:
            return {'erro': 'Nenhuma questão ativa'}
        
        resposta_correta = session.resposta_correta
        proxima_questao = self.nova_questao(nome_usuario)
        
        return {
            'resposta_correta': resposta_correta,
            'proxima_questao': proxima_questao.get('questao') if not proxima_questao.get('erro') else None
        }
    
    def get_ranking(self):
        # Retorna ranking por pontuação
        users_ordenados = sorted(
            self.users_sessions.values(), 
            key=lambda x: x.pontuacao, 
            reverse=True
        )
        
        return [
            {
                'posicao': i + 1,
                'nome_usuario': user.nome_usuario,
                'pontuacao': user.pontuacao,
                'acertos': user.acertos,
                'questoes_respondidas': user.questoes_respondidas
            }
            for i, user in enumerate(users_ordenados[:10])
        ]