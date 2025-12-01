🧠 QuizBot PE
Chatbot Educativo e Interativo sobre Pernambuco

Projeto Integrador II — ADS / Senac
Tema: Deep Learning aplicado a Educação e Cultura Pernambucana

👥 Equipe
Nome	Função Principal
Ruan Guedes	Front-end Web / Documentação
Erick Carrasco	Visão Computacional
Antonio Lemos	Banco de Dados / API
Gabriel Afonso	Backend / Infra
João Lucas	NLP / Backend
Jairo Marinho	Dataset e Treinamento
Dandara Gouveia	Pesquisa e Conteúdo
🎯 Objetivo Geral

Desenvolver um jogo educativo gamificado que estimule o aprendizado sobre turismo, cultura e história de Pernambuco, utilizando:

Tecnologia	Função
🤖 Deep Learning (YOLOv8)	Reconhecimento do local na imagem
🧠 IA Generativa	Explicação cultural sobre o lugar
💬 Processamento de Linguagem Natural	Interação com usuário
🕹️ Gamificação	Pontuação e desafios
🌐 Interface Web	Acessível e interativa

O usuário envia uma foto de um ponto turístico, e o QuizBot tenta adivinhar o local e explicá-lo de forma educativa — tudo com feedback em tempo real.

⚙️ Arquitetura do Sistema
flowchart LR
A[Usuário no Frontend] --> B[Envio da Imagem]
B --> C[API Flask]
C --> D[Modelo YOLOv8 - Visão]
C --> E[Modelo LLM - PLN/Explicação]
D --> C
E --> C
C --> F[Retorno com Local + Explicação + Pontuação]
F --> A

💻 Tecnologias Utilizadas
Backend

Python + Flask

YOLOv8 (Ultralytics)

OpenAI API (ou Mistral, dependendo do ambiente)

Tratamento de imagens (Pillow / OpenCV)

Frontend

HTML / CSS / JavaScript

Consumo de API via Fetch

Infra

Render (Deploy)

GitHub Actions (CI/CD)

🧪 Deep Learning — Dataset e Treinamento

Criamos um dataset próprio com imagens turísticas de PE

Classes (locais):

Itamaracá

Paço do Frevo

Instituto Ricardo Brennand

Porto de Galinhas

Marco Zero

Oficina Brennand

Treinamento:

Modelo: YOLOv8n

Epochs: 50

Metric mAP50: ↑ Atingimos precisão satisfatória

Desafio superado: limpeza do dataset, balanceamento e correção de rótulos 👏

🕹️ Como Jogar

1️⃣ Faça upload ou tire uma foto de algum ponto turístico de Pernambuco
2️⃣ O bot tenta reconhecer o local pela imagem
3️⃣ Se acertar → você ganha pontos e recebe uma explicação cultural
4️⃣ Se errar → pode tentar novamente 😁

🔧 Como Rodar Localmente
# Clonar o repositório
git clone https://github.com/ruanpedroguedes/quizbot-educativo-pe.git
cd quizbot-educativo-pe

# Criar ambiente
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar backend
cd backend
python app.py

# Abrir o frontend
cd ../frontend
open index.html  # Windows: start index.html


Upload da Imagem	Resposta + Explicação
🖼️	🧠 + 🎯
🔗 Deploy Online

🚀 Possíveis Evoluções (Roadmap)

 Nova base com mais cidades e pontos turísticos

 Ranking global de jogadores e login

 Suporte por voz (fala → texto)

 Modos temáticos: História, Praias, Cultura…

 Tradução para inglês e espanhol

 Transformar em app mobile (React Native)



