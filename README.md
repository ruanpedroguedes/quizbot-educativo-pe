# 🧠 QuizBot PE  
### Chatbot Educativo e Interativo sobre Pernambuco

> **Projeto Integrador II — ADS / Senac**  
> **Tema:** Deep Learning aplicado a Educação e Cultura Pernambucana  

---

## 👥 Equipe

| Nome | Função Principal |
|------|-----------------|
| **Ruan Guedes** | Front-end Web / Documentação |
| **Erick Carrasco** | Visão Computacional / Front-end Web |
| **Antonio Lemos** | Banco de Dados / API |
| **Gabriel Afonso** | Backend / Infra |
| **João Lucas** | NLP / Backend |
| **Jairo Marinho** | Dataset e Treinamento |
| **Dandara Gouveia** | Pesquisa e Conteúdo |

---

## 🎯 Objetivo Geral

Desenvolver um **jogo educativo gamificado** que estimule o aprendizado sobre **turismo, cultura e história de Pernambuco**, utilizando:

| Tecnologia | Função |
|----------|--------|
| 🤖 Deep Learning (YOLOv8) | Reconhecimento do local na imagem |
| 🧠 IA Generativa | Explicação cultural sobre o lugar |
| 💬 PLN | Interação com usuário |
| 🕹️ Gamificação | Pontuação e desafios |
| 🌐 Interface Web | Acessível e interativa |

O usuário envia uma **foto de um ponto turístico**, e o QuizBot tenta **adivinhar o local** e explicá-lo de forma educativa — tudo com feedback em tempo real.

---


💻 Tecnologias Utilizadas
Backend

Python + Flask

YOLOv8 (Ultralytics)

OpenAI API (ou Mistral)

Pillow / OpenCV

Frontend

HTML / CSS / JavaScript

Consumo de API com Fetch

Infra

Render (Deploy)

GitHub Actions (CI/CD)

🧪 Deep Learning — Dataset e Treinamento

Dataset próprio com 6 classes de pontos turísticos de Pernambuco:

Itamaracá

Marco Zero

Paço do Frevo

Instituto Ricardo Brennand

Oficina Cerâmica Brennand

Porto de Galinhas

Treinamento:

Modelo: YOLOv8n

Epochs: 50

Balanceamento e padronização do dataset

Métricas atingidas: mAP50 satisfatório para o MVP

🕹️ Como Jogar

1️⃣ Faça upload ou tire uma foto de um ponto turístico de Pernambuco
2️⃣ O bot tenta reconhecer o local pela imagem
3️⃣ Se acertar → ganha pontos + explicação histórica/cultural
4️⃣ Se errar → pode tentar novamente


# Clonar o repositório
git clone https://github.com/ruanpedroguedes/quizbot-educativo-pe.git
cd quizbot-educativo-pe

# Criar ambiente virtual
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

# Arquitetura do Sistema
flowchart LR
    U[Usuário<br>📱💻] --> FE[Frontend<br>HTML/CSS/JS]

    FE --> API[(Flask API)]

    subgraph Back-end
        API --> GS[Game State<br>Regras e Pontuação]
        API --> TP[Text Processor<br>Geração de perguntas e respostas]
        API --> IP[Image Processor<br>Pré-processamento e YOLOv8]
    end

    IP --> YOLO[(YOLOv8<br>Reconhecimento do Local)]
    TP --> NLP[(IA Generativa<br>Explicações Culturais)]
    
    YOLO --> DB[(Dataset PE<br>Imagens e Labels)]
    DB --> YOLO

    GS --> FE
    NLP --> FE



# Estrutura de Pastas
📁 quizbot-educativo-pe/
│
├── backend/
│   ├── datasets/
│   │   └── dataset_pernambuco_25_turistico.csv
│   ├── imagens/                   # Dataset visual para o modelo
│   ├── preprocessing/
│   │   └── pre_processor_img.py   # Pipeline de pré-processamento de imagem
│   ├── quiz_system/
│   │   ├── app.py                 # Lógica do quiz e rotas principais
│   │   └── game_state.py          # Controle de pontuação e progresso
│   ├── text_processor/
│   │   ├── perguntas_respostas.py # Base de perguntas/explicações
│   │   └── pre_processor_text.py  # Tratamento de texto
│   ├── server.py                  # Servidor Flask (deploy)
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── home.html
│   ├── login.html
│   ├── personagens.html
│   ├── styles.css
│   ├── app.js
│   ├── assets/                    # Sons e imagens da interface
│   └── audio.js
│
└── README.md



