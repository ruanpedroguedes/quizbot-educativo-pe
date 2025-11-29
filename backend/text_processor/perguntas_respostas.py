from text_processor.pre_processor_text import QuestionProcessor
from sklearn.metrics.pairwise import cosine_similarity
import random
import pandas as pd

class QuizSystem:
    def __init__(self):
        self.processor = QuestionProcessor()
        self.df = None
        self.question_embeddings = None
        self.tags_index = {}
        self.quiz_ativo = False
        self.pergunta_atual = None
        self.resposta_correta = None
        self.dica_atual = None
        self.pontuacao = 0
        self.tentativas = 0

    def treinamento(self, df):
        self.df = df.copy()
        
        combined_texts = [
            f"{pergunta} [SEP] {contexto}" for pergunta, contexto in zip(df['pergunta'], df['contexto'])
        ]

        self.question_embeddings = self.processor.get_embeddings(combined_texts)
        self._construir_indice_tags()

    def _construir_indice_tags(self):
        self.tags_index = {}
        
        if 'tags' not in self.df.columns:
            print("⚠️  Aviso: Coluna 'tags' não encontrada no dataset")
            return
        
        tags_count = 0
        for idx, row in self.df.iterrows():
            tags = row['tags']
            
            if tags and isinstance(tags, list) and len(tags) > 0:
                for tag in tags:
                    if tag and isinstance(tag, str):
                        tag_limpa = tag.lower().strip()
                        if tag_limpa:
                            if tag_limpa not in self.tags_index:
                                self.tags_index[tag_limpa] = []
                            self.tags_index[tag_limpa].append(idx)
                            tags_count += 1
        
        print(f"✅ Índice de tags construído com {len(self.tags_index)} tags únicas")

    def iniciar_quiz(self, tema=None):
        if tema:
            # Busca por tema específico
            resultados = self._buscar_por_tema(tema)
        else:
            # Quiz aleatório
            resultados = list(range(len(self.df)))
        
        if not resultados:
            return False, "Não encontrei locais sobre esse tema. Tente outro!"
        
        # Escolhe um local aleatório
        if isinstance(resultados, list) and len(resultados) > 0:
            if isinstance(resultados[0], int):  # São índices
                idx_escolhido = random.choice(resultados)
            else:  # São resultados completos
                idx_escolhido = random.choice(resultados)['indice']
        else:
            idx_escolhido = random.randint(0, len(self.df) - 1)
        
        # Configura o quiz
        self.quiz_ativo = True
        self.pergunta_atual = self.df.iloc[idx_escolhido]['pergunta']
        self.resposta_correta = self.df.iloc[idx_escolhido]['contexto']
        self.dica_atual = self._gerar_dica(self.df.iloc[idx_escolhido])
        self.tentativas = 0
        
        # Prepara a pergunta do quiz
        pergunta_quiz = f"🎯 **QUIZ**: {self.pergunta_atual}\n\n"
        pergunta_quiz += f"💡 **Dica**: {self.dica_atual}\n\n"
        pergunta_quiz += "🔍 **Tente adivinhar: Qual é este local?**"
        
        return True, pergunta_quiz

    def _buscar_por_tema(self, tema):
        tema_lower = tema.lower()
        
        # Verifica se é uma tag existente
        if tema_lower in self.tags_index:
            return self.tags_index[tema_lower]
        
        # Busca por similaridade no texto
        resultados_similaridade = self.melhor_resposta(tema, top_k=10)
        return [r['indice'] for r in resultados_similaridade]

    def _gerar_dica(self, local_info):
        contexto = local_info['contexto']
        tags = local_info.get('tags', [])
        
        dicas = []
        
        # Dica baseada no contexto
        palavras = contexto.split()
        if len(palavras) > 5:
            dicas.append(f"Tem {len([p for p in palavras if len(p) > 3])} características principais")
        
        # Dica baseada em tags
        if tags:
            tags_faceis = [tag for tag in tags if tag in ['praia', 'cidade', 'parque', 'museu', 'igreja']]
            if tags_faceis:
                dicas.append(f"É um {tags_faceis[0]}")
        
        # Dica de localização
        if 'recife' in contexto.lower():
            dicas.append("Fica na capital de Pernambuco")
        elif 'olinda' in contexto.lower():
            dicas.append("É uma cidade histórica próximo ao Recife")
        elif 'noronha' in contexto.lower():
            dicas.append("É um arquipélago famoso")
        
        # Dica de comprimento
        nome_local = self._extrair_nome_local(contexto)
        if nome_local:
            dicas.append(f"O nome tem {len(nome_local.split())} palavra(s)")
        
        return random.choice(dicas) if dicas else "É um local turístico de Pernambuco"

    def _extrair_nome_local(self, contexto):
        # Palavras comuns para remover
        palavras_comuns = ['fica', 'localizado', 'situado', 'encontra-se', 'é um', 'é uma', 'no', 'na', 'em']
        palavras = contexto.split()
        
        # Pega as primeiras palavras (provavelmente contém o nome)
        nome = ' '.join(palavras[:4])
        
        for palavra in palavras_comuns:
            nome = nome.replace(palavra, '').strip()
        
        return nome if len(nome) > 3 else "Local"

    def verificar_resposta(self, resposta_usuario):
        if not self.quiz_ativo:
            return False, "Nenhum quiz ativo. Use 'quiz' para começar!"
        
        self.tentativas += 1
        
        # Calcula similaridade entre resposta e resposta correta
        resposta_embedding = self.processor.get_embeddings([resposta_usuario])
        correta_embedding = self.processor.get_embeddings([self.resposta_correta])
        
        similaridade = cosine_similarity(resposta_embedding, correta_embedding)[0][0]
        
        if similaridade > 0.7:
            # Resposta correta!
            self.pontuacao += 1
            self.quiz_ativo = False
            
            mensagem = f"🎉 **CORRETO!** Parabéns!\n\n"
            mensagem += f"📍 **Local:** {self.resposta_correta}\n"
            mensagem += f"🏆 **Pontuação:** {self.pontuacao} ponto(s)\n"
            mensagem += f"🎯 **Tentativas:** {self.tentativas}"
            
            return True, mensagem
            
        elif similaridade > 0.5 and self.tentativas == 1:
            # Quase acertou na primeira tentativa
            dica_extra = self._gerar_dica_extra()
            return False, f"⚠️ **Quase lá!** {dica_extra}\n\nTente novamente:"
        
        elif similaridade > 0.4:
            # Resposta relacionada
            return False, "❌ **Não é isso, mas você está no caminho certo!**\n\nTente novamente:"
        
        else:
            # Resposta muito diferente
            if self.tentativas >= 2:
                dica_extra = self._gerar_dica_extra()
                return False, f"❌ **Não é isso.** {dica_extra}\n\nTente novamente:"
            else:
                return False, "❌ **Não é esse local.** Tente novamente:"

    def _gerar_dica_extra(self):
        dicas_extra = [
            "Pense em locais famosos de Pernambuco...",
            "Dica: é um ponto turístico muito visitado!",
            "Tente lembrar das belezas naturais ou históricas...",
            "Dica: muitas pessoas tiram fotos neste lugar!",
            "Pense em patrimônios culturais ou naturais..."
        ]
        return random.choice(dicas_extra)

    def desistir(self):
        if not self.quiz_ativo:
            return "Nenhum quiz ativo."
        
        self.quiz_ativo = False
        return f"😔 **A resposta era:** {self.resposta_correta}\n\n🏆 **Sua pontuação atual:** {self.pontuacao}"

    def get_pontuacao(self):
        return f"🏆 **Pontuação:** {self.pontuacao} ponto(s)"

    def resetar_pontuacao(self):
        self.pontuacao = 0
        return "🔄 Pontuação resetada! 🏆 0 pontos"

    # Métodos auxiliares para busca (mantidos da versão anterior)
    def melhor_resposta(self, user_question, top_k=3):
        if self.question_embeddings is None:
            raise ValueError("Sistema ainda não treinado.")

        user_embeddings = self.processor.get_embeddings([user_question])
        similaridades = cosine_similarity(user_embeddings, self.question_embeddings)[0]
        top_indices = similaridades.argsort()[-top_k:][::-1]

        resultados = []
        for idx in top_indices:
            resultados.append({
                'pergunta': self.df.iloc[idx]['pergunta'],
                'contexto': self.df.iloc[idx]['contexto'],
                'similaridade': similaridades[idx],
                'indice': idx,
                'tags': self.df.iloc[idx].get('tags', [])
            })

        return resultados

    def listar_temas(self):
        """Lista temas/tags disponíveis para quiz"""
        if not self.tags_index:
            return "Nenhum tema disponível."
        
        temas = sorted(list(self.tags_index.keys()))
        return f"🎯 **Temas disponíveis:** {', '.join([f'#{tema}' for tema in temas])}"