import uuid
from datetime import datetime
import json
import os
from urllib.parse import urlparse
from text_processor.perguntas_respostas import QuestionProcessor
from preprocessing.pre_processor_img import ImageProcessor 
from quiz_system.game_state import UserGameState
from sklearn.metrics.pairwise import cosine_similarity
import random
import torch
import pandas as pd

try:
    from train_model import LocalImageClassifier
except ImportError:
    print("⚠️  Módulo train_model não encontrado - usando modo fallback")
    LocalImageClassifier = None

class QuizSystem:
    def __init__(self, model_path=None, api_base_url="http://localhost:8000"):
        self.processor = QuestionProcessor()
        self.image_processor = ImageProcessor() 
        self.df = None
        self.question_embeddings = None
        self.locais_embeddings = None
        self.users_sessions = {}  # {nome_usuario: UserGameState}
        self.imagens_processadas = {} # cache das imagens processadas
        self.api_base_url = api_base_url 

        # Carregar modelo treinado
        self.classification_model = None
        if model_path and os.path.exists(model_path) and LocalImageClassifier is not None:
            try:
                self.classification_model = LocalImageClassifier.load_model(model_path)
                print("✅ Modelo de classificação carregado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao carregar modelo: {e}")
                self.classification_model = None

    def _para_url_api(self, caminho_local):
        #Converte caminho local para URL da API
        if caminho_local.startswith('http'):
            return caminho_local  
        
        nome_arquivo = os.path.basename(caminho_local)
        return f"{self.api_base_url}/imagens/{nome_arquivo}"            
        
    def treinamento(self, df):
        self.df = df.copy()
        
        print("🔄 Pré-computando embeddings...")
        
        # Embeddings para os nomes dos locais (validação de resposta)
        nomes_locais = self._extrair_nomes_locais(df)
        self.locais_embeddings = self.processor.get_embeddings(nomes_locais)
        
        # Pré-Processamento de imagens
        if not self.classification_model:
            self._preprocessar_imagens_dataset()

        print(f"✅ Sistema treinado com {len(df)} locais!")
    
    def _preprocessar_imagens_dataset(self):
        try:
            # Extrai todos os caminhos de imagem únicos
            caminhos_imagens = []
            for idx, row in self.df.iterrows():
                if 'imagem' in row and row['imagem'] is not None and row['imagem'] != '':
                    # Se for uma lista, pega todas as URLs
                    if isinstance(row['imagem'], list):
                        for url in row['imagem']:
                            if pd.notna(url) and url and isinstance(url, str):
                                caminho_local = self._para_caminho_local(url)
                                if caminho_local and os.path.exists(caminho_local):
                                    caminhos_imagens.append(caminho_local)
               # Se for uma string única 
                    elif isinstance(row['imagem'], str) and row['imagem'].strip():
                        caminho_local = self._para_caminho_local(row['imagem'].strip())
                        if caminho_local and os.path.exists(caminho_local):
                            caminhos_imagens.append(caminho_local)
            
            # Remove duplicatas
            caminhos_imagens = list(set(caminhos_imagens))
            
            print(f"🔄 Processando {len(caminhos_imagens)} imagens...")

            if not caminhos_imagens:
                print("⚠️  Nenhuma imagem válida encontrada no dataset")
                return
            
            # Processa cada imagem
            imagens_sucesso = 0
            for i, url in enumerate(caminhos_imagens):
                try:
                    print(f"📸 [{i+1}/{len(caminhos_imagens)}] Processando: {url}")
                    tensor = self.image_processor.process_single_image(url)
                    if tensor is not None:
                        self.imagens_processadas[url] = tensor
                        imagens_sucesso += 1
                        print(f"✅ Imagem processada: {url}")
                    else:
                        print(f"❌ Falha ao processar imagem: {url}")
                except Exception as e:
                    print(f"❌ Erro ao processar {url}: {e}")
            
            print(f"🎉 Pré-processamento de imagens concluído: {imagens_sucesso}/{len(caminhos_imagens)} processadas com sucesso")
                
        except Exception as e:
            print(f"❌ Erro no pré-processamento de imagens: {e}")

    def _extrair_nomes_locais(self, df):
        #Extrai os nomes principais dos locais para validação
        nomes = []
        for contexto in df['contexto']:
            # Extrai o nome do local do contexto (primeiras palavras)
            nome = contexto.split('.')[0]  # Pega até o primeiro ponto
            nome = nome.split(' é ')[0]    # Remove descrições
            nome = nome.split(' fica ')[0] # Remove localizações
            nome = nome.split(' localizado ')[0]
            nomes.append(nome.strip())
        return nomes
    
    def criar_ou_recuperar_sessao(self, nome_usuario):
        """Cria uma nova sessão ou recupera existente pelo nome"""
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
        """Retorna estatísticas do usuário"""
        if nome_usuario not in self.users_sessions:
            return None
        return self.users_sessions[nome_usuario].to_dict()
    
    def nova_questao(self, nome_usuario, tema=None):
        if nome_usuario not in self.users_sessions:
            return {'erro': 'Usuário não encontrado. Crie uma sessão primeiro.'}
        
        session = self.users_sessions[nome_usuario]
        return self._nova_questao_legado(session)
    
    def _nova_questao_legado(self, session):
        #Método legado baseado em similaridade
        max_tentativas = 10
        for tentativa in range(max_tentativas):
            idx = random.randint(0, len(self.df) - 1)
            local = self.df.iloc[idx]

            # Processa imagem sob demanda
            imagem_path = self._obter_imagem_local(local)
            if imagem_path and os.path.exists(imagem_path):
                imagem_tensor = self.image_processor.process_single_image(imagem_path)
                
                if imagem_tensor is not None:
                    imagem_url = self._para_url_api(imagem_path)
                    
                    session.questao_atual = {
                        'id': idx,
                        'pergunta': "Que local é esse da imagem?",
                        'imagem': imagem_url,  
                        'imagem_tensor': imagem_tensor,
                        'dica': self._gerar_dica_identificacao(local),
                        'tags': local.get('tags', []),
                        'dificuldade': self._calcular_dificuldade(local),
                        'resposta_correta': local['contexto'],
                        'nome_local': self._extrair_nome_do_contexto(local['contexto']),
                        'caminho_local': imagem_path  
                    }
                    session.resposta_correta = local['contexto']
                    session.tentativas = 0
                    
                    return {
                        'questao': session.questao_atual,
                        'session_id': session.session_id,
                        'modo': 'legado'
                    }
        
        return {'erro': 'Não foi possível gerar uma questão com imagem no momento.'}
    
    def _listar_imagens_locais(self):
        #Lista todas as imagens disponíveis localmente
        imagens = []
        diretorios = ['backend/dataset', 'backend/imagens']
        
        for diretorio in diretorios:
            if os.path.exists(diretorio):
                for root, dirs, files in os.walk(diretorio):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            imagens.append(os.path.join(root, file))
        
        return imagens
    
    def _encontrar_local_por_nome(self, nome_local):
        #Encontra um local no dataframe pelo nome
        for idx, row in self.df.iterrows():
            contexto_nome = self._extrair_nome_do_contexto(row['contexto'])
            if contexto_nome.lower() == nome_local.lower():
                return row
        return None
    
    def _obter_imagem_local(self, local):
        #Obtém caminho de imagem local a partir dos dados do local
        if 'imagem' in local and pd.notna(local['imagem']):
            if isinstance(local['imagem'], list) and local['imagem']:
                imagem_path = random.choice(local['imagem'])
            elif isinstance(local['imagem'], str) and local['imagem'].strip():
                imagem_path = local['imagem'].strip()
            else:
                return None
            
            # Torna o caminho local
            return self._para_caminho_local(imagem_path)
        return None
    
    def _para_caminho_local(self, caminho):
        #Converte URL/path para caminho local
        if caminho.startswith('http'):
            # Extrai nome do arquivo da URL
            parsed = urlparse(caminho)
            nome_arquivo = os.path.basename(parsed.path) 

            if '?' in nome_arquivo:
                nome_arquivo = nome_arquivo.split('?')[0]
            
            # Procura em vários diretórios possíveis
            diretorios_procura = [
                'backend/imagens',
                'backend/dataset', 
                'imagens',
                'dataset'
            ]

            for diretorio in diretorios_procura:
                caminho_local = os.path.join(diretorio, nome_arquivo)
                if os.path.exists(caminho_local):
                    print(f"✅ Encontrada imagem local: {caminho_local}")
                    return caminho_local
                
            print(f"❌ Imagem não encontrada localmente: {nome_arquivo}")
            return None
        else:
            # Já é um caminho local
            if os.path.exists(caminho):
                return caminho
            return None
    
    def _calcular_dificuldade(self, local):
        #Calcula dificuldade baseada no contexto
        contexto = local['contexto']
        palavras = len(contexto.split())
        
        if palavras < 10:
            return "Fácil"
        elif palavras < 20:
            return "Médio"
        else:
            return "Difícil"
    
    def _gerar_dica_identificacao(self, local):
        #Gera dicas específicas para identificação de imagem
        contexto = local['contexto']
        tags = local.get('tags', [])
        
        dicas = []
        
        # Dica baseada em tags
        if tags:
            tags_faceis = [tag for tag in tags if tag in ['praia', 'cidade', 'parque', 'museu', 'igreja', 'centro', 'histórico']]
            if tags_faceis:
                dicas.append(f"💡 É um {tags_faceis[0]}")
        
        # Dica baseada no tipo de local
        contexto_lower = contexto.lower()
        if any(word in contexto_lower for word in ['praia', 'mar', 'litoral']):
            dicas.append("🌊 Fica no litoral")
        elif any(word in contexto_lower for word in ['museu', 'histórico', 'patrimônio']):
            dicas.append("🏛️ Local histórico")
        elif any(word in contexto_lower for word in ['parque', 'natureza', 'verde']):
            dicas.append("🌳 Área natural")
        elif any(word in contexto_lower for word in ['centro', 'cidade', 'urbano']):
            dicas.append("🏙️ Área urbana")
        
        # Dica da localização
        if 'recife' in contexto_lower:
            dicas.append("📍 Fica no Recife")
        elif 'olinda' in contexto_lower:
            dicas.append("📍 Fica em Olinda")
        elif 'noronha' in contexto_lower:
            dicas.append("📍 Arquipélago famoso")
        
        # Dica do nome (número de palavras)
        nome = self._extrair_nome_do_contexto(contexto)
        if nome and len(nome.split()) > 1:
            dicas.append(f"📝 O nome tem {len(nome.split())} palavras")
        elif nome:
            dicas.append(f"📝 Começa com '{nome[0].upper()}'")
        
        return random.choice(dicas) if dicas else "💡 Ponto turístico famoso de Pernambuco"
    
    def _extrair_nome_do_contexto(self, contexto):
        #Extrai o nome do local do contexto
        # Remove descrições comuns
        descricoes = ['é um', 'é uma', 'fica', 'localizado', 'situado', 'conhecido']
        nome = contexto.split('.')[0]
        
        for desc in descricoes:
            if desc in nome:
                nome = nome.split(desc)[0]
        
        return nome.strip()
    
    def validar_resposta_identificacao(self, nome_usuario, resposta_usuario):
        #Valida a resposta para identificação de imagem e retorna info completa
        if nome_usuario not in self.users_sessions:
            return {'valido': False, 'erro': 'Usuário não encontrado'}
        
        session = self.users_sessions[nome_usuario]
        
        if not session.questao_atual:
            return {'valido': False, 'erro': 'Nenhuma questão ativa'}
        
        session.tentativas += 1
        session.questoes_respondidas += 1
        
        # Calcula similaridade entre resposta e nome do local correto
        resposta_embedding = self.processor.get_embeddings([resposta_usuario])[0]
        nome_correto = session.questao_atual['nome_local']
        nome_correto_embedding = self.processor.get_embeddings([nome_correto])[0]
        
        similaridade = cosine_similarity([resposta_embedding], [nome_correto_embedding])[0][0]
        
        print(f"🔍 Validando: '{resposta_usuario}' vs '{nome_correto}' - Similaridade: {similaridade:.3f}")
        
        # Threshold para identificação 
        threshold = 0.65
        
        if similaridade > threshold:
            # Prepara resposta completa
            pontos = self._calcular_pontos_identificacao(similaridade, session.tentativas)
            session.pontuacao += pontos
            session.acertos += 1
            
            # Busca informações completas do local
            info_local = self._obter_informacoes_completas(session.questao_atual['id'])
            
            session.historico.append({
                'tipo': 'identificacao_imagem',
                'questao': session.questao_atual['pergunta'],
                'imagem': session.questao_atual['imagem'],
                'resposta_usuario': resposta_usuario,
                'resposta_correta': session.resposta_correta,
                'nome_correto': nome_correto,
                'tentativas': session.tentativas,
                'similaridade': float(similaridade),
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
                'nome_local_correto': nome_correto,
                'tentativas': session.tentativas,
                'similaridade': float(similaridade),
                'feedback': self._gerar_feedback_identificacao(similaridade),
                'informacoes_local': info_local,  
                'proxima_questao': proxima_questao.get('questao') if not proxima_questao.get('erro') else None
            }
        
        else:
            # Não acertou
            return {
                'valido': True,
                'acertou': False,
                'feedback': self._gerar_feedback_erro_identificacao(similaridade, session.tentativas),
                'tentativas': session.tentativas,
                'similaridade': float(similaridade),
                'dica_extra': session.questao_atual['dica'] if session.tentativas >= 2 else None
            }
    
    def _obter_informacoes_completas(self, id_local):
        #Retorna informações completas sobre o local
        try:
            local = self.df.iloc[id_local]
            
            # Formata informações de forma educativa
            informacoes = {
                'nome': self._extrair_nome_do_contexto(local['contexto']),
                'descricao_completa': local['contexto'],
                'curiosidades': self._gerar_curiosidades(local),
                'tags': local.get('tags', []),
                'dica_turistica': self._gerar_dica_turistica(local),
                'imagem': local.get('imagem', '')
            }
            
            return informacoes
            
        except Exception as e:
            print(f"❌ Erro ao obter informações do local: {e}")
            return None
    
    def _gerar_curiosidades(self, local):
        #Gera curiosidades baseadas no contexto
        contexto = local['contexto'].lower()
        tags = local.get('tags', [])
        curiosidades = []
        
        # Curiosidades baseadas no conteúdo
        if any(word in contexto for word in ['patrimônio', 'unesco', 'histórico']):
            curiosidades.append("🏛️ É um Patrimônio Histórico ou Cultural")
        
        if any(word in contexto for word in ['praia', 'mar', 'litoral']):
            curiosidades.append("🌊 Local perfeito para banho e fotos")
        
        if any(word in contexto for word in ['natureza', 'parque', 'verde']):
            curiosidades.append("🌳 Ótimo para contato com a natureza")
        
        if any(word in contexto for word in ['famoso', 'conhecido', 'visitado']):
            curiosidades.append("⭐ Um dos pontos mais visitados da região")
        
        # Curiosidades baseadas em tags
        if 'gastronomia' in tags:
            curiosidades.append("🍽️ Oferece opções de gastronomia local")
        
        if 'cultura' in tags:
            curiosidades.append("🎭 Local com rica programação cultural")
        
        if 'aventura' in tags:
            curiosidades.append("🚀 Ideal para atividades de aventura")
        
        return curiosidades[:3]  # Limita a 3 curiosidades
    
    def _gerar_dica_turistica(self, local):
        #Gera dica turística prática
        contexto = local['contexto'].lower()
        
        if any(word in contexto for word in ['praia', 'mar']):
            return "💡 Dica: Leve protetor solar e aproveite o pôr do sol!"
        
        elif any(word in contexto for word in ['museu', 'histórico']):
            return "💡 Dica: Visite durante a semana para evitar filas!"
        
        elif any(word in contexto for word in ['parque', 'natureza']):
            return "💡 Dica: Use roupas confortáveis e leve água!"
        
        elif any(word in contexto for word in ['centro', 'cidade']):
            return "💡 Dica: Melhor visitar durante o dia para aproveitar o comércio local!"
        
        else:
            return "💡 Dica: Não esqueça a câmera para registrar o momento!"
    
    def _calcular_pontos_identificacao(self, similaridade, tentativas):
        #Calcula pontos para identificação (mais pontos por ser mais difícil)
        base_points = 150  # Base maior
        similarity_bonus = int(similaridade * 75)  # Bônus maior
        speed_bonus = max(0, 75 - (tentativas * 25))  # Bônus por velocidade
        
        return base_points + similarity_bonus + speed_bonus
    
    def _gerar_feedback_identificacao(self, similaridade):
        #Gera feedback para acerto na identificação
        if similaridade > 0.85:
            return "🎉 **PERFEITO!** Você identificou com precisão!"
        elif similaridade > 0.75:
            return "✅ **EXCELENTE!** Quase perfeito!"
        elif similaridade > 0.65:
            return "👍 **MUITO BOM!** Identificou corretamente!"
        else:
            return "👏 **CERTO!** Você acertou o local!"
    
    def _gerar_feedback_erro_identificacao(self, similaridade, tentativas):
        #Gera feedback para erro na identificação
        if tentativas == 1:
            if similaridade > 0.5:
                return "❌ Quase! Mas não é exatamente esse local..."
            else:
                return "❌ Não é esse local... Tente novamente!"
        elif tentativas == 2:
            return "❌ Ainda não... Observe bem a imagem e pense em locais famosos!"
        else:
            return "❌ Vamos tentar de outra forma... Que tal uma dica?"
    
    def desistir(self, nome_usuario):
        #Revela a resposta e gera nova questão
        if nome_usuario not in self.users_sessions:
            return {'erro': 'Usuário não encontrado'}
        
        session = self.users_sessions[nome_usuario]
        
        if not session.questao_atual:
            return {'erro': 'Nenhuma questão ativa'}
        
        resposta_correta = session.resposta_correta
        info_local = self._obter_informacoes_completas(session.questao_atual['id'])
        proxima_questao = self.nova_questao(nome_usuario)
        
        return {
            'resposta_correta': resposta_correta,
            'informacoes_local': info_local,
            'proxima_questao': proxima_questao.get('questao') if not proxima_questao.get('erro') else None
        }
    
    def get_ranking(self):
        #Retorna ranking por pontuação
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
    
    # Método de validação 
    def validar_resposta(self, nome_usuario, resposta_usuario, imagem_usuario=None):
        #Método legado 
        return self.validar_resposta_identificacao(nome_usuario, resposta_usuario)