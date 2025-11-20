from text_processor.pre_processor_text import QuestionProcessor
from sklearn.metrics.pairwise import cosine_similarity
import random
import pandas as pd
import numpy as np

class QuestionAnswerSystem:
    def __init__(self):
        self.processor = QuestionProcessor()
        self.df = None
        self.question_embeddings = None
        self.context_embeddings = None
        self.tags_index = {}

    def treinamento(self, df):
        self.df = df.copy()
        
        combined_texts = [
            f"{pergunta} [SEP] {contexto}" for pergunta, contexto in zip(df['pergunta'], df['contexto'])
        ]

        self.question_embeddings = self.processor.get_embeddings(combined_texts)
        self._construir_indice_tags()

    def _construir_indice_tags(self):
        """Constrói índice invertido para busca por tags - CORRIGIDO"""
        self.tags_index = {}
        
        if 'tags' not in self.df.columns:
            print("⚠️  Aviso: Coluna 'tags' não encontrada no dataset")
            return
        
        tags_count = 0
        for idx, row in self.df.iterrows():
            tags = row['tags']
            
            # CORREÇÃO: Verifica se tags não é vazio de forma segura
            if tags and isinstance(tags, list) and len(tags) > 0:
                for tag in tags:
                    if tag and isinstance(tag, str):  # Verifica se tag é string não vazia
                        tag_limpa = tag.lower().strip()
                        if tag_limpa:  # Verifica se não é string vazia após limpeza
                            if tag_limpa not in self.tags_index:
                                self.tags_index[tag_limpa] = []
                            self.tags_index[tag_limpa].append(idx)
                            tags_count += 1
        
        print(f"✅ Índice de tags construído com {len(self.tags_index)} tags únicas e {tags_count} associações")

    def _extrair_tags_da_pergunta(self, pergunta):
        """Extrai tags da pergunta do usuário"""
        pergunta_lower = pergunta.lower()
        tags_encontradas = []
        
        # Mapeamento específico para turismo em Pernambuco
        mapeamento_tags = {
            'noronha': ['noronha', 'fernando', 'fernando de noronha'],
            'praia': ['praia', 'praias', 'mar', 'litoral', 'areia', 'onda', 'praiana', 'balneário'],
            'mergulho': ['mergulho', 'mergulhar', 'scuba', 'snorkel', 'água', 'marinho'],
            'natureza': ['natureza', 'natural', 'ecológico', 'verde', 'parque', 'reserva'],
            'historia': ['histórico', 'história', 'museu', 'antigo', 'colonial', 'patrimônio'],
            'cultura': ['cultura', 'cultural', 'arte', 'folclore', 'tradição', 'artístico'],
            'gastronomia': ['comida', 'culinária', 'restaurante', 'gastronomia', 'prato', 'culinario'],
            'aventura': ['aventura', 'esporte', 'radical', 'trilha', 'cachoeira', 'esportivo'],
            'turismo': ['turismo', 'turístico', 'passeio', 'visita', 'pontos turísticos'],
            'recife': ['recife', 'recifense', 'capital'],
            'olinda': ['olinda', 'olindense'],
            'porto': ['porto', 'porto de galinhas'],
            'boa viagem': ['boa viagem', 'praia de boa viagem']
        }
        
        # 1. Busca por tags exatas do mapeamento
        for tag_categoria, palavras_chave in mapeamento_tags.items():
            for palavra in palavras_chave:
                if palavra in pergunta_lower:
                    tags_encontradas.append(tag_categoria)
                    break
        
        # 2. Busca direta nas tags do índice
        for tag_existente in self.tags_index.keys():
            if tag_existente in pergunta_lower and tag_existente not in tags_encontradas:
                tags_encontradas.append(tag_existente)
        
        return list(set(tags_encontradas))

    def buscar_por_tags(self, tags_usuario):
        """Busca locais que contenham as tags especificadas"""
        if not self.tags_index:
            return []
            
        resultados = []
        tags_procuradas = [tag.lower().strip() for tag in tags_usuario]
        
        for tag in tags_procuradas:
            if tag in self.tags_index:
                for idx in self.tags_index[tag]:
                    # Evita duplicatas
                    if idx not in [r['indice'] for r in resultados]:
                        resultado = {
                            'pergunta': self.df.iloc[idx]['pergunta'],
                            'contexto': self.df.iloc[idx]['contexto'],
                            'similaridade': 0.7,
                            'indice': idx,
                            'tipo_busca': 'tag',
                            'tags': self.df.iloc[idx].get('tags', [])
                        }
                        resultados.append(resultado)
        
        return resultados

    def melhor_resposta(self, user_question, top_k=3, usar_tags=True):
        if self.question_embeddings is None:
            raise ValueError("Sistema ainda não treinado.")

        # 1. Busca tradicional por similaridade
        user_embeddings = self.processor.get_embeddings([user_question])
        similaridades = cosine_similarity(user_embeddings, self.question_embeddings)[0]
        top_indices = similaridades.argsort()[-top_k:][::-1]

        resultados_similaridade = []
        for idx in top_indices:
            resultados_similaridade.append({
                'pergunta': self.df.iloc[idx]['pergunta'],
                'contexto': self.df.iloc[idx]['contexto'],
                'similaridade': similaridades[idx],
                'indice': idx,
                'tipo_busca': 'similaridade',
                'tags': self.df.iloc[idx].get('tags', [])
            })

        # 2. Busca por tags se habilitado
        if usar_tags and self.tags_index:
            tags_encontradas = self._extrair_tags_da_pergunta(user_question)
            
            if tags_encontradas:
                print(f"🔍 Tags detectadas: {tags_encontradas}")
                resultados_tags = self.buscar_por_tags(tags_encontradas)
                
                if resultados_tags:
                    todos_resultados = self._combinar_resultados(resultados_similaridade, resultados_tags)
                    return todos_resultados[:top_k]

        return resultados_similaridade

    def _combinar_resultados(self, resultados_similaridade, resultados_tags):
        """Combina e ranqueia resultados de similaridade e tags"""
        todos_resultados = []
        
        for resultado in resultados_similaridade:
            resultado['score_combinado'] = resultado['similaridade']
            todos_resultados.append(resultado)
        
        for resultado_tag in resultados_tags:
            ja_existe = any(r['indice'] == resultado_tag['indice'] for r in resultados_similaridade)
            if not ja_existe:
                resultado_tag['score_combinado'] = resultado_tag['similaridade']
                todos_resultados.append(resultado_tag)
        
        todos_resultados.sort(key=lambda x: x['score_combinado'], reverse=True)
        return todos_resultados

    def listar_tags(self):
        """Retorna lista de todas as tags disponíveis"""
        if not self.tags_index:
            return "Nenhuma tag disponível no dataset."
        
        tags_unicas = sorted(list(self.tags_index.keys()))
        tags_formatadas = [f"#{tag}" for tag in tags_unicas]
        return f"🏷️ **Tags disponíveis:** {', '.join(tags_formatadas)}"

    def formatar_resposta(self, resultado):
        contexto = resultado['contexto']
        similaridade = resultado['similaridade']
        tags = resultado.get('tags', [])
        tipo_busca = resultado.get('tipo_busca', 'similaridade')
        
        confianca = f"{similaridade * 100:.1f}%"
        
        respostas_possiveis = [
            f"🏖️  {contexto}",
            f"📍 {contexto}",
            f"🌴 {contexto}",
            f"🎯 {contexto}",
            f"💫 {contexto}"
        ]
        
        resposta_base = random.choice(respostas_possiveis)
        
        if tags:
            tags_formatadas = self._formatar_tags(tags)
            resposta_base += f"\n🏷️  **Categorias:** {tags_formatadas}"
        
        if similaridade > 0.8:
            resposta_base += f"\n💡 **Confiança:** {confianca}"
        elif similaridade > 0.6:
            resposta_base += f"\n⚠️  **Confiança:** {confianca}"
        else:
            resposta_base += f"\n🤔 **Confiança:** {confianca}"
        
        if tipo_busca == 'tag':
            resposta_base += f"\n🔍 *Encontrado por categorias relacionadas*"
        
        return resposta_base

    def _formatar_tags(self, tags):
        """Formata as tags de forma bonita"""
        if isinstance(tags, list):
            return " ".join([f"#{tag}" for tag in tags])
        return f"#{tags}"

    def formatar_multiplas_respostas(self, resultados):
        """Formata múltiplos resultados como recomendações"""
        if len(resultados) == 1:
            return self.formatar_resposta(resultados[0])
        
        resposta = "🎯 **Encontrei várias opções para você:**\n\n"
        
        for i, resultado in enumerate(resultados, 1):
            tags_str = self._formatar_tags(resultado.get('tags', []))
            confianca = f"{resultado['similaridade'] * 100:.1f}%"
            
            resposta += f"{i}️⃣ **{resultado['pergunta']}**\n"
            resposta += f"   📍 {resultado['contexto']}\n"
            if tags_str:
                resposta += f"   🏷️  {tags_str}\n"
            resposta += f"   📊 {confianca}\n\n"
        
        tags_comuns = set()
        for resultado in resultados:
            if resultado.get('tags'):
                tags_comuns.update(resultado['tags'])
        
        if tags_comuns:
            resposta += f"💡 **Dica:** Explore mais sobre: {self._formatar_tags(list(tags_comuns))}"
        
        return resposta

    def buscar_por_tag_especifica(self, tag):
        """Busca todos os locais com uma tag específica"""
        if not self.tags_index:
            return []
            
        tag = tag.lower().strip()
        if tag not in self.tags_index:
            return []
        
        resultados = []
        for idx in self.tags_index[tag]:
            resultados.append({
                'pergunta': self.df.iloc[idx]['pergunta'],
                'contexto': self.df.iloc[idx]['contexto'],
                'similaridade': 0.8,
                'indice': idx,
                'tipo_busca': 'tag_especifica',
                'tags': self.df.iloc[idx].get('tags', [])
            })
        
        return resultados