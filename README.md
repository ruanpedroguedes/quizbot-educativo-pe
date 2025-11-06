# 🧠 QuizBot PE – Chatbot Educativo e Interativo sobre Pernambuco

### Projeto Integrador II — Senac | Deep Learning

**Integrantes:**

* Ruan Guedes
* Erick Carrasco
* Antonio Lemos
* Gabriel Afonso
* João Lucas
* Jairo Marinho
* Dandara Gouveia

---

## 🎯 Objetivo Geral

Criar um **chatbot com inteligência artificial e interface web interativa**, que funcione como um **jogo educativo (quiz)** sobre **turismo e história de Pernambuco**, integrando:

* 🖼️ **Reconhecimento de imagens** enviadas pelo usuário (Visão Computacional)
* 💬 **Interpretação e resposta** a perguntas em linguagem natural (PLN)
* 📚 **Geração de explicações didáticas** sobre o conteúdo da imagem
* 🎮 **Gamificação**, tornando o aprendizado mais divertido e acessível

---

## 📅 Entregas

| Entrega       | Data                                | Descrição                      |
| ------------- | ----------------------------------- | ------------------------------ |
| **Entrega 1** | 03/11 (Turma 30) / 04/11 (Turma 29) | Protótipo inicial              |
| **Entrega 2** | 01/12 (Turma 30) a 27/12 (Turma 29) | Aplicativo completo (NLP + CV) |


1. Arquitetura do Sistema e Fluxo de Dados (Pipeline)

Este diagrama mostra a arquitetura principal da aplicação, seguindo a jornada do usuário e o pipeline de dados.
graph TD
    %% Definição dos 4 Componentes Principais (Subgraphs)
    subgraph "1. FRONTEND (UI Streamlit)"
        direction TD
        Jornada_A["<i class='fa fa-user-check'></i> Login"] --> Jornada_B("<i class='fa fa-user-astronaut'></i> Seleção de Personagem")
        Jornada_B --> Jornada_C{"<i class='fa fa-comments'></i> Chatbot UI"}
        Jornada_C_Fim("<i class='fa fa-trophy'></i> Pontuação/Fim de Jogo")
    end
    
    subgraph "2. BACKEND (Orquestração Python)"
        direction TD
        B_A[Recebe API Call:<br>Imagem + Pergunta]
        B_A --> B_B{"<i class='fa fa-gamepad'></i> Lógica do Quiz e Pontuação"}
    end
    
    subgraph "3. MODELOS DE IA (Pytorch / Transformers)"
        direction TD
        M_CV["<i class='fa fa-images'></i> <b>Visão Computacional</b><br>(ResNet-50)"]
        M_NLP["<i class='fa fa-brain'></i> <b>NLP - QA</b><br>(Hugging Face Transformers)"]
    end
    
    subgraph "4. DATA (Base de Conhecimento)"
        direction TD
        D_JSON["<i class='fa fa-database'></i> <b>dataset_pernambuco.json</b><br>(Contextos para RAG)"]
        D_IMG["<i class='fa fa-file-image'></i> <b>Dataset de Imagens</b><br>(Imagens de Treinamento)"]
    end

    %% FLUXO PRINCIPAL (PIPELINE)
    
    %% 1. Extração
    Jornada_C -- "<b>1. Extração</b><br>(Input do Usuário)" --> B_A
    
    %% 2. Transformação e Carga (CV)
    B_A -- "<b>2. Transformação (Imagem)</b><br>(Redimensiona/Normaliza)" --> M_CV
    M_CV -- "Consulta (Treino)" --> D_IMG
    M_CV -- "<b>3. Carga (Identificação)</b><br>Retorna 'chave_local'" --> B_B
    
    %% 3. Transformação e Carga (NLP)
    B_B -- "Busca Contexto (RAG)" --> D_JSON
    D_JSON -- "Retorna Contexto (Texto)" --> M_NLP
    B_A -- "<b>2. Transformação (Pergunta)</b><br>(Tokeniza/Limpa)" --> M_NLP
    
    %% 4. Resposta
    M_NLP -- "<b>3. Carga (Resposta)</b><br>Retorna 'resposta_texto'" --> B_B
    B_B -- "<b>4. Resposta (Consolidada)</b><br>Envia Resposta + Pontos" --> Jornada_C
    B_B -- "Lógica de Fim de Jogo" --> Jornada_C_Fim


    2. Ciclo de Vida do Projeto e Avaliação

Este diagrama mostra as macro-etapas do projeto e como os modelos serão avaliados.

graph TD
    subgraph "ETAPAS DO PROJETO"
        E1[<i class='fa fa-lightbulb'></i> Ideação e Design] --> E2[<i class='fa fa-book'></i> Estudo e Dataset]
        E2 --> E3[<i class='fa fa-code'></i> Code e Deploy]
    end

    subgraph "ESTRATÉGIAS DE AVALIAÇÃO"
        direction LR
        A_CV["<b>Modelo CV (ResNet-50)</b>"]
        A_NLP["<b>Modelo Linguagem (QA)</b>"]
        
        A_CV -- "Acurácia" --> M_CV_A["% Total de Acertos"]
        A_CV -- "Matriz de Confusão" --> M_CV_B["Quais locais são confundidos"]
        
        A_NLP -- "Acurácia" --> M_NLP_A["% Total de Acertos"]
        A_NLP -- "F1-Score (QA)" --> M_NLP_B["Sobreposição de Palavras<br>(Previsto vs. Correto)"]
    end
