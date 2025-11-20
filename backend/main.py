from text_processor.perguntas_respostas import QuestionAnswerSystem
import pandas as pd

def main():
    qa_system = QuestionAnswerSystem()

    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json') 
    qa_system.treinamento(df)

    print("🤖 Bem-vindo ao Assistente de Turismo de Pernambuco!")
    print("💡 Digite 'sair' para encerrar\n")
    
    while True: 
        user_question = input("👤 Você: ").strip()
        
        if user_question.lower() == 'sair':
            print("🤖 Até logo! Espero ter ajudado! 🏖️")
            break

        results = qa_system.melhor_resposta(user_question)  
        
        if results:
            melhor_resultado = results[0]
            resposta_formatada = qa_system.formatar_resposta(melhor_resultado)
            
            print(f"\n🤖 Bot: {resposta_formatada}")
            
            # Mostra similaridade técnica (opcional)
            # print(f"\n📊 [DEBUG] Similaridade: {melhor_resultado['similaridade']:.4f}")
            
        else:
            print("🤖 Bot: Desculpe, não encontrei informações sobre isso. Pode reformular?")
        
if __name__ == "__main__":
    main()