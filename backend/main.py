from text_processor.perguntas_respostas import QuestionAnswerSystem
import pandas as pd

def main():
    qa_system = QuestionAnswerSystem()

    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json') 
    qa_system.treinamento(df)

    print("🏖️  Bem-vindo ao Assistente de Turismo de Pernambuco!")
    print("💡 **Comandos disponíveis:**")
    print("   - 'tags' → Ver todas as categorias")
    print("   - 'tag [nome]' → Buscar por tag específica (ex: 'tag praia')")
    print("   - 'sair' → Encerrar")
    print()
    
    while True: 
        user_input = input("👤 Você: ").strip()
        
        if user_input.lower() == 'sair':
            print("🤖 Até logo! Boas viagens! 🌴")
            break
        elif user_input.lower() == 'tags':
            print(f"\n🤖 {qa_system.listar_tags()}\n")
            continue
        elif user_input.lower().startswith('tag '):
            tag_especifica = user_input[4:].strip()
            if tag_especifica:
                resultados = qa_system.buscar_por_tag_especifica(tag_especifica)
                if resultados:
                    resposta = qa_system.formatar_multiplas_respostas(resultados)
                    print(f"\n🤖 Bot: {resposta}\n")
                else:
                    print(f"\n🤖 Bot: Nenhum local encontrado com a tag '{tag_especifica}'\n")
            continue
            
        # Busca normal com suporte a tags
        results = qa_system.melhor_resposta(user_input, top_k=3, usar_tags=True)
        
        if results:
            # Decide o formato da resposta
            melhor_similaridade = results[0]['similaridade']
            
            if len(results) > 1 and melhor_similaridade > 0.5:
                resposta_formatada = qa_system.formatar_multiplas_respostas(results)
            else:
                resposta_formatada = qa_system.formatar_resposta(results[0])
            
            print(f"\n🤖 Bot: {resposta_formatada}\n")
        else:
            print("🤖 Bot: Desculpe, não encontrei informações sobre isso. Tente usar outras palavras ou explore as tags!\n")
            
if __name__ == "__main__":
    main()