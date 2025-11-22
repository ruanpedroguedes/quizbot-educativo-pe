from text_processor.perguntas_respostas import QuizSystem
import pandas as pd

def main():
    quiz_system = QuizSystem()

    df = pd.read_json('datasets/dataset_pernambuco_25_turistas.json') 
    quiz_system.treinamento(df)

    print("🎯 BEM-VINDO AO QUIZ TURÍSTICO DE PERNAMBUCO!")
    print("=" * 50)
    print("COMO JOGAR:")
    print("• 'quiz' - Quiz aleatório")
    print("• 'quiz [tema]' - Quiz sobre um tema (ex: 'quiz praia')")
    print("• 'pontos' - Ver sua pontuação")
    print("• 'desistir' - Revelar resposta atual")
    print("• 'reset' - Resetar pontuação")
    print("• 'temas' - Ver temas disponíveis")
    print("• 'sair' - Encerrar")
    print("=" * 50)
    
    while True: 
        user_input = input("\n🎮 Comando: ").strip()
        
        if user_input.lower() == 'sair':
            print(f"\n🏆 Pontuação final: {quiz_system.get_pontuacao()}")
            print("Obrigado por jogar! Até a próxima! 🌴")
            break
            
        elif user_input.lower() == 'pontos':
            print(f"\n🤖 {quiz_system.get_pontuacao()}")
            
        elif user_input.lower() == 'reset':
            print(f"\n🤖 {quiz_system.resetar_pontuacao()}")
            
        elif user_input.lower() == 'desistir':
            print(f"\n🤖 {quiz_system.desistir()}")
            
        elif user_input.lower() == 'temas':
            print(f"\n🤖 {quiz_system.listar_temas()}")
            
        elif user_input.lower().startswith('quiz'):
            # Processa comando de quiz
            partes = user_input.split()
            if len(partes) == 1:
                # Quiz aleatório
                sucesso, mensagem = quiz_system.iniciar_quiz()
            else:
                # Quiz com tema
                tema = ' '.join(partes[1:])
                sucesso, mensagem = quiz_system.iniciar_quiz(tema)
            
            print(f"\n🤖 {mensagem}")
            
            # Se quiz foi iniciado com sucesso, aguarda resposta
            if sucesso:
                while quiz_system.quiz_ativo:
                    resposta = input("\n💭 Sua resposta: ").strip()
                    
                    if resposta.lower() == 'desistir':
                        print(f"\n🤖 {quiz_system.desistir()}")
                        break
                    elif resposta.lower() == 'sair':
                        print(f"\n🏆 Pontuação final: {quiz_system.get_pontuacao()}")
                        exit()
                    else:
                        acertou, feedback = quiz_system.verificar_resposta(resposta)
                        print(f"\n🤖 {feedback}")
                        
                        if acertou:
                            # Pergunta se quer continuar
                            continuar = input("\n🎮 Jogar novamente? (s/n): ").strip().lower()
                            if continuar in ['s', 'sim', 'yes']:
                                sucesso, mensagem = quiz_system.iniciar_quiz()
                                print(f"\n🤖 {mensagem}")
                            else:
                                break
            
        else:
            print("\n🤖 Comando não reconhecido. Use 'quiz' para começar ou 'ajuda' para ver comandos.")

if __name__ == "__main__":
    main()