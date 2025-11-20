from text_processor.pre_processor_text import QuestionProcessor
from sklearn.metrics.pairwise import cosine_similarity
import random

class QuestionAnswerSystem:
    def __init__(self):
        self.processor = QuestionProcessor()
        self.df = None
        self.question_embeddings = None
        self.context_embeddings = None

    def treinamento(self, df):
        self.df = df.copy()
        
        combined_texts = [
            f"{pergunta} [SEP] {contexto}" for pergunta, contexto in zip(df['pergunta'], df['contexto'])
        ]

        self.question_embeddings = self.processor.get_embeddings(combined_texts)      

    # Função pra encontrar a melhor resposta
    def melhor_resposta(self, user_question, top_k=3):
        if self.question_embeddings is None:
            raise ValueError("Sistema ainda não treinado.")

        # Embedding pra pergunta do usuário
        user_embeddings = self.processor.get_embeddings([user_question])

        similaridades = cosine_similarity(user_embeddings, self.question_embeddings)[0]

        top_indices = similaridades.argsort()[-top_k:][::-1]

        resultado = []
        for idx in top_indices:
            resultado.append({
                'pergunta': self.df.iloc[idx]['pergunta'],
                'contexto': self.df.iloc[idx]['contexto'],
                'similaridade': similaridades[idx],
                'indice': idx
            })

        return resultado
    
    def formatar_resposta(self, resultado):
        pergunta = resultado['pergunta']
        contexto = resultado['contexto']
        similaridade = resultado['similaridade']
        
        # Converte similaridade para porcentagem
        confianca = f"{similaridade * 100:.1f}%"
        
        # Gera respostas baseadas no contexto encontrado
        respostas_possiveis = [
            f"Baseado no que sei: {contexto}",
            f"Encontrei esta informação: {contexto}",
            f"Segundo meus dados: {contexto}",
            f"Aqui está o que conheço: {contexto}",
            f"Com base nas informações: {contexto}"
        ]
        
        # Escolhe uma resposta aleatória
        import random
        resposta_base = random.choice(respostas_possiveis)
        
        # Adiciona nível de confiança
        if similaridade > 0.8:
            resposta_base += f"\n\n💡 **Estou {confianca} confiante nesta resposta**"
        elif similaridade > 0.6:
            resposta_base += f"\n\n⚠️ **Estou {confianca} confiante**"
        else:
            resposta_base += f"\n\n🤔 **Encontrei algo similar ({confianca} de confiança)**"
        
        return resposta_base