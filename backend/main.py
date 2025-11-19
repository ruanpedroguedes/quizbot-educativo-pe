from text_processor.perguntas_respostas import QuestionAnswerSystem
import pandas as pd

def main():
    qa_system = QuestionAnswerSystem()

    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json')

    qa_system.treinamento(df)

    # Testar com pergunta
    while True: 
        user_question = input("\nDigite sua pergunta: ")
        
        if user_question.lower() == 'sair':
            break

        results = qa_system.melhor_resposta(user_question)  
        
        print(f"\nPergunta: {user_question}")
        print("Respostas encontradas:")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Resultado {i} (Similaridade: {result['similaridade']:.4f}) ---")
            print(f"Pergunta similar: {result['pergunta']}")
            print(f"Contexto: {result['contexto']}")
            
if __name__ == "__main__":
    main()