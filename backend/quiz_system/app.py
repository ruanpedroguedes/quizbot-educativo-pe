import uuid
from datetime import datetime
import json
from text_processor.perguntas_respostas import QuestionProcessor
from preprocessing.pre_processor_img import ImageProcessor 
from quiz_system.game_state import UserGameState
from sklearn.metrics.pairwise import cosine_similarity
import random
import torch
import pandas as pd

class QuizSystem:
    def __init__(self):
        self.processor = QuestionProcessor()
        self.image_processor = ImageProcessor() 
        self.df = None
        self.question_embeddings = None
        self.locais_embeddings = None
        self.users_sessions = {}  # {nome_usuario: UserGameState}
        self.imagens_processadas = {} # cache das imagens processadas
        
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
        
        #Pré-Processamento de imagens
        self._preprocessar_imagens_dataset()

        print(f"✅ Sistema treinado com {len(df)} locais!")
    
    def _preprocessar_imagens_dataset(self):
        try:
            # Extrai todos os caminhos de imagem únicos
            caminhos_imagens = []
            for idx, row in self.df.iterrows():
                if 'imagem' in row and pd.notna(row['imagem']):
                    caminhos_imagens.append(row['imagem'])
            
            # Remove duplicatas
            caminhos_imagens = list(set(caminhos_imagens))
            
            print(f" Processando {len(caminhos_imagens)} imagens...")
            
            # Processa em lotes para melhor performance
            batch_size = 10
            for i in range(0, len(caminhos_imagens), batch_size):
                batch = caminhos_imagens[i:i + batch_size]
                tensors = self.image_processor.process_img(batch)
                
                if tensors is not None:
                    for j, caminho in enumerate(batch):
                        self.imagens_processadas[caminho] = tensors[j]
                        print(f"✅ Imagem processada: {caminho}")
                
                print(f" Progresso: {min(i + batch_size, len(caminhos_imagens))}/{len(caminhos_imagens)}")
                
        except Exception as e:
            print(f"❌ Erro no pré-processamento de imagens: {e}")

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

        # OBTÉM IMAGEM PROCESSADA
        imagem_tensor = None
        imagem_path = local.get('imagem', '')
        if imagem_path and imagem_path in self.imagens_processadas:
            imagem_tensor = self.imagens_processadas[imagem_path]
            print(f"✅ Imagem carregada do cache: {imagem_path}")
        elif imagem_path:
            # Processa sob demanda se não estava no cache
            imagem_tensor = self.image_processor.process_single_image(imagem_path)
            if imagem_tensor is not None:
                self.imagens_processadas[imagem_path] = imagem_tensor
                print(f"✅ Imagem processada sob demanda: {imagem_path}")
        
        # Prepara a questão
        session.questao_atual = {
            'id': idx,
            'pergunta': local['pergunta'],
            'imagem': imagem_path,
            'imagem_tensor': imagem_tensor,
            'dica': self._gerar_dica_inteligente(local),
            'tags': local.get('tags', []),
            'dificuldade': self._calcular_dificuldade(local),
            'caracteristicas_visuais': self._extrair_caracteristicas_visuais(local, imagem_tensor)
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
    
      
    def _extrair_caracteristicas_visuais(self, local, imagem_tensor):
        caracteristicas = []
        
        if imagem_tensor is not None:
            # Analisa características da imagem processada
            try:
                # Exemplo: detecta cores predominantes (simplificado)
                if imagem_tensor.mean() > 0.6:
                    caracteristicas.append("Local bem iluminado")
                else:
                    caracteristicas.append("Local com tons mais escuros")
                
            except Exception as e:
                print(f"⚠️ Erro na análise visual: {e}")
        
        # Características baseadas no contexto textual
        contexto = local['contexto'].lower()
        if any(word in contexto for word in ['praia', 'mar', 'oceano', 'litoral']):
            caracteristicas.append("Ambiente costeiro")
        if any(word in contexto for word in ['histórico', 'antigo', 'século', 'patrimônio']):
            caracteristicas.append("Arquitetura histórica")
        if any(word in contexto for word in ['moderno', 'contemporâneo', 'novo']):
            caracteristicas.append("Arquitetura moderna")
        if any(word in contexto for word in ['natureza', 'verde', 'árvore', 'parque']):
            caracteristicas.append("Área verde/natural")
        
        return caracteristicas[:3] 
    
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

        #Características visuais das fotos
        caracteristicas_visuais = self._extrair_caracteristicas_visuais(local, None)
        
        dicas = []
        
        # Dica baseada em tags
        if tags:
            dicas.append(f"🏷️ Tags: {', '.join(tags[:3])}")

        #Dica Baseada na foto
        if caracteristicas_visuais:
            dica_visual = random.choice(caracteristicas_visuais)
            dicas.append(f"👀 {dica_visual}")
        
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
    
    def validar_resposta(self, nome_usuario, resposta_usuario, imagem_usuario=None):
        # Valida a resposta do usuário usando Deep Learning
        if nome_usuario not in self.users_sessions:
            return {'valido': False, 'erro': 'Usuário não encontrado'}
        
        session = self.users_sessions[nome_usuario]
        
        if not session.questao_atual:
            return {'valido': False, 'erro': 'Nenhuma questão ativa'}
        
        session.tentativas += 1
        session.questoes_respondidas += 1
         
        # Validação por texto (similaridade semântica)
        resposta_embedding = self.processor.get_embeddings([resposta_usuario])[0]
        
        similaridade_correta = cosine_similarity(
            [resposta_embedding], 
            [session.resposta_embedding]
        )[0][0]
        
        # Validação por Imagem (se o usuário enviou uma imagem)
        similaridade_imagem = 0.0
        if imagem_usuario:
            similaridade_imagem = self._validar_imagem_usuario(imagem_usuario, session.questao_atual['imagem_tensor'])
            print(f"🔍 Similaridade da imagem: {similaridade_imagem:.3f}")
        
        # Combina as Similaridades
        similaridade_final = self._combinar_similaridades(similaridade_correta, similaridade_imagem, imagem_usuario is not None)
        
        print(f" Similaridades - Texto: {similaridade_correta:.3f}, Imagem: {similaridade_imagem:.3f}, Final: {similaridade_final:.3f}")
        
        # Validação inteligente com threshold adaptável
        threshold = 0.72  # Pode ajustar baseado na dificuldade
        
        if similaridade_final > threshold:
            # Acertou!
            pontos = self._calcular_pontos(similaridade_final, session.tentativas, similaridade_imagem)
            session.pontuacao += pontos
            session.acertos += 1
            
            session.historico.append({
                'questao': session.questao_atual['pergunta'],
                'resposta_usuario': resposta_usuario,
                'resposta_correta': session.resposta_correta,
                'tentativas': session.tentativas,
                'similaridade_texto': float(similaridade_correta),
                'similaridade_imagem': float(similaridade_imagem),
                'similaridade_final': float(similaridade_final),
                'pontos_ganhos': pontos,
                'timestamp': datetime.now().isoformat(),
                'usou_imagem': imagem_usuario is not None
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
                'similaridade_texto': float(similaridade_correta),
                'similaridade_imagem': float(similaridade_imagem),
                'similaridade_final': float(similaridade_final),
                'feedback': self._gerar_feedback_positivo(similaridade_correta, similaridade_imagem),
                'proxima_questao': proxima_questao.get('questao') if not proxima_questao.get('erro') else None
            }
        
        else:
            # Não acertou
            return {
                'valido': True,
                'acertou': False,
                'feedback': self._gerar_feedback_negativo(similaridade_correta, session.tentativas),
                'tentativas': session.tentativas,
                'similaridade_texto': float(similaridade_correta),
                'similaridade_imagem': float(similaridade_imagem),
                'dica_extra': session.questao_atual['dica'] if session.tentativas >= 2 else None
            }
    def _validar_imagem_usuario(self, imagem_usuario, imagem_correta_tensor):
        #Valida similaridade entre imagens usando processamento
        try:
            # Processa a imagem do usuário
            imagem_usuario_tensor = self.image_processor.process_single_image(imagem_usuario)
            
            if imagem_usuario_tensor is None or imagem_correta_tensor is None:
                return 0.0
            
            #Calcula similaridade entre os tensores 
            similarity = torch.nn.functional.cosine_similarity(
                imagem_usuario_tensor.flatten(), 
                imagem_correta_tensor.flatten(), 
                dim=0
            )
            
            return similarity.item()
            
        except Exception as e:
            print(f"❌ Erro na validação de imagem: {e}")
            return 0.0
    
    def _combinar_similaridades(self, similaridade_texto, similaridade_imagem, usou_imagem):
        #Combina similaridades de texto e imagem
        if usou_imagem:
            # Se usou imagem, dá peso para ambos
            return 0.7 * similaridade_texto + 0.3 * similaridade_imagem
        else:
            # Se só texto, usa apenas similaridade textual
            return similaridade_texto
    
    def _calcular_pontos(self, similaridade, tentativas, similaridade_imagem):
        # Calcula pontos baseados na qualidade da resposta e tentativas
        base_points = 100
        similarity_bonus = int(similaridade * 50)  # Até 50 pontos extra por precisão
        speed_bonus = max(0, 50 - (tentativas * 20))  # Bonus por menos tentativas
        image_bonus = int(similaridade_imagem * 30) if similaridade_imagem > 0 else 0  
        
        return base_points + similarity_bonus + speed_bonus + image_bonus
    
    def _gerar_feedback_positivo(self, similaridade_texto, similaridade_imagem):
        if similaridade_imagem > 0.9:
            return "🎉 Perfeito! Sua descrição e imagem combinam perfeitamente!"
        elif similaridade_texto > 0.8:
            return "✅ Excelente! Quase perfeito!"
        elif similaridade_texto > 0.75:
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
    def get_info_imagem(self, caminho_imagem):
        #Retorna informações sobre uma imagem processada
        if caminho_imagem in self.imagens_processadas:
            tensor = self.imagens_processadas[caminho_imagem]
            return {
                'processada': True,
                'shape': tuple(tensor.shape),
                'caminho': caminho_imagem
            }
        else:
            return {
                'processada': False,
                'caminho': caminho_imagem
            }