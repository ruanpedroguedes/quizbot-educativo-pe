# --- Importações de Bibliotecas ---
import streamlit as st  # A biblioteca principal para criar a interface web
import time             # Usada para simular o tempo de resposta do backend
import sys              # Usado para manipular o 'path' do sistema
import os               # Usado para interagir com o sistema operacional (ex: caminhos de arquivos)

# --- Configuração da Página ---
# st.set_page_config() deve ser o primeiro comando Streamlit executado.
# Define configurações globais da página.
st.set_page_config(
    layout="centered",  # CORREÇÃO: "centered" em vez de "wide"
    page_title="QuizBot PE", # Título que aparece na aba do navegador
    page_icon="🧠"             # Emoji que aparece na aba do navegador
)

# --- Bloco de importação do Backend ---
# Esta é uma parte crucial para projetos com subpastas.
# 1. Pegamos o caminho do diretório atual (onde 'main.py' está: 'app/')
# 2. Voltamos um nível ('..') para chegar na pasta raiz ('projeto_chatbot_multimodal/')
# 3. Adicionamos esse caminho raiz ao 'sys.path' (lista de locais onde o Python busca módulos)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Agora que a pasta raiz está no path, podemos importar do 'backend'
try:
    # Tentamos importar a função real do backend
    from backend.chatbot import responder_mensagem
    BACKEND_DISPONIVEL = True # Flag para sabermos que o backend está funcionando
    st.toast("Backend conectado!", icon="✅") # CORREÇÃO: Trocado de st.sidebar para st.toast
except ImportError:
    # Se a importação falhar (arquivo não existe, erro no código, etc.)
    BACKEND_DISPONIVEL = False # Avisamos o app que o backend não está disponível
    st.toast("Backend não encontrado. Rodando em modo simulação.", icon="🤖") # CORREÇÃO: Trocado de st.sidebar para st.toast
# --- Fim do Bloco de Importação ---


# --- CSS Customizado ---
# Injetamos uma string gigante de CSS usando st.markdown()
# Isso nos permite estilizar o app além do que o Streamlit oferece por padrão.
STYLE_CSS = """
<style>
/* Oculta elementos padrão do Streamlit (menu hamburguer, header, footer) */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Define o fundo escuro e a cor da fonte para toda a aplicação */
body, .main {
    background-color: #0E0E0E !important; /* !important força a sobreposição */
    color: white;
}

/* Container principal do Streamlit. Removemos preenchimentos padrão */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* --- Estilos da Tela de Login --- */

/* O "card" (cartão) que segura o conteúdo do login */
.login-card {
    background-color: #1E1E1E;
    padding: 40px 50px 50px 50px; /* Espaçamento interno */
    border-radius: 15px;         /* Bordas arredondadas */
    max-width: 480px;            /* Largura máxima do card */
    margin: 10vh auto;           /* Centraliza horizontalmente e dá margem no topo */
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); /* Sombra */
}

/* O container do input (para remover fundos brancos) */
.login-card [data-testid="stTextInput"] > div > div {
    background-color: #333333; /* Cor do input */
    border-radius: 8px;
    border: 1px solid #333333;
}

/* O input em si (texto, padding) */
.login-card [data-testid="stTextInput"] input {
    background-color: #333333 !important;
    color: white;
    padding-top: 1.25rem;
    padding-bottom: 1.25rem;
    /* Remove a borda padrão do streamlit no input */
    border: none; 
    box-shadow: none;
}

/* O label (texto "Senha", "E-mail...") */
.login-card [data-testid="stTextInput"] label {
    color: #B0B0B0;
    padding-left: 5px;
}

/* Botão de Login */
.login-card [data-testid="stButton"] > button { 
    background-color: #4B00E0; 
    color: white; 
    font-weight: bold; 
    border: none; 
    border-radius: 8px; 
    padding: 12px 0; 
    width: 100%; 
    margin-top: 20px; 
    transition: background-color 0.3s; 
}
.login-card [data-testid="stButton"] > button:hover { background-color: #5E1FFF; }
.login-card [data-testid="stButton"] > button:focus { 
    background-color: #5E1FFF; 
    color: white; 
    border: none; 
    box-shadow: none; 
}
.login-card .card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 25px; }
.login-card .card-footer a { font-size: 14px; color: #B0B0B0; text-decoration: none; }
.login-card .card-footer a:hover { color: white; }
.login-card .card-footer img { width: 35px; height: auto; }


/* --- Estilos da Tela de Seleção de Personagem --- */

/* Container que segura os 3 cards de personagem e o botão "Voltar" */
.character-select-container { 
    max-width: 900px; /* Largura máxima para os 3 cards */
    margin: 5vh auto; /* Centraliza o container na tela */
    text-align: center; /* AJUSTE: Centraliza o st.divider e o botão "Voltar" */
}
.character-select-title { 
    font-size: 32px; 
    font-weight: bold; 
    text-align: center; 
    margin-bottom: 40px; 
}
/* Card individual do personagem */
.character-card { 
    background-color: #1E1E1E; 
    padding: 30px; 
    border-radius: 15px; 
    text-align: center; /* Centraliza o conteúdo (título, imagem, botão) */
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); 
    transition: transform 0.3s; /* Efeito de hover */
    height: 100%; /* Garante que os 3 cards tenham a mesma altura */
    display: flex; /* Permite alinhar o botão no final */
    flex-direction: column; 
    justify-content: space-between; /* Joga o botão "Começar" para baixo */
}
.character-card:hover { transform: translateY(-5px); /* Efeito de "levantar" */ }
.character-card h3 { font-size: 20px; font-weight: bold; margin-bottom: 20px; }
.character-card img { 
    width: 150px; 
    height: 200px; 
    object-fit: contain; /* Garante que a imagem caiba sem distorcer */
    margin: 0 auto 25px auto; /* Centraliza a imagem */
    image-rendering: pixelated; /* Mantém a arte pixelada nítida */
}
/* Botão "Começar" branco (dentro do card de personagem) */
.character-card [data-testid="stButton"] > button { 
    background-color: #FFFFFF; 
    color: #1E1E1E !important; /* Cor do texto escura */
    font-weight: bold; 
    border: none; 
    border-radius: 8px; 
    padding: 12px 0; 
    width: 100%; 
    margin-top: 10px; 
    transition: background-color 0.3s; 
}
.character-card .stButton > button:hover { background-color: #F0F0F0; }


/* --- Estilos da Tela do Chatbot --- */

/* O card principal que segura a interface de chat */
.chat-window {
    max-width: 800px;
    margin: 0 auto; /* Centraliza o card na tela */
    background-color: #1E1E1E;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    height: 85vh; /* Altura fixa (85% da altura da tela) */
    display: flex; /* Layout flexível para organizar header, history e input */
    flex-direction: column;
}

/* Header do chat (onde fica a pontuação) */
.chat-header {
    background-color: #333333;
    padding: 15px 25px;
    border-top-left-radius: 15px; /* Arredonda cantos superiores */
    border-top-right-radius: 15px;
    border-bottom: 1px solid #444; /* Linha divisória */
}
.chat-header span { font-weight: bold; font-size: 18px; color: #FFFFFF; }
.chat-header img { width: 20px; margin-left: 5px; vertical-align: middle; }

/* Container para o st.file_uploader (upload de imagem) */
.uploader-container {
    padding: 0 25px; /* Alinha com o padding do header */
    margin-top: 20px;
}
/* Estilizando o botão de upload */
.uploader-container [data-testid="stFileUploader"] > label {
    border: 1px dashed #4B00E0; /* Borda pontilhada roxa */
    background-color: #333333;
    border-radius: 10px;
}
.uploader-container [data-testid="stFileUploader"] svg {
    color: #4B00E0; /* Cor do ícone */
}
/* Oculta o nome do arquivo após o upload (opcional, mas limpa a UI) */
.uploader-container [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    display: none;
}

/* Container do histórico de mensagens */
.chat-history-container {
    flex-grow: 1; /* Faz esta div ocupar todo o espaço vertical disponível */
    overflow-y: auto; /* Adiciona uma barra de rolagem se as mensagens estourarem a altura */
    padding: 20px;
}

/* Estilizando os balões de chat (componente nativo st.chat_message) */
.stChatMessage {
    background-color: #333333;
    border-radius: 10px;
    padding: 12px 15px;
    margin-bottom: 10px;
    border: none;
}
/* Balão do usuário (direita) */
[data-testid="chat-message-container-user"] .stChatMessage {
    background-color: #4B00E0; /* Roxo/Azul do design */
    color: white;
}
/* Balão do bot (esquerda) */
[data-testid="chat-message-container-assistant"] .stChatMessage {
    background-color: #3A3A3A;
    color: white;
}
/* Remove o fundo padrão transparente do *container* do balão (melhora visual) */
[data-testid="chat-message-container"] > div {
    background-color: transparent;
    border: none;
    box-shadow: none;
}

/* A barra de input (componente nativo st.chat_input) */
[data-testid="stChatInput"] {
    background-color: #1E1E1E; /* Fundo igual ao do card */
    border-top: 1px solid #444;
    padding: 15px 20px 25px 20px;
    border-bottom-left-radius: 15px; /* Arredonda cantos inferiores */
    border-bottom-right-radius: 15px;
}
[data-testid="stChatInput"] > div { /* A caixa de texto interna */
    background-color: #333333;
    border: none;
    border-radius: 10px;
}
[data-testid="stChatInput"] > div > input { /* O texto digitado */
    color: white;
}
/* Placeholder text do chat input */
[data-testid="stChatInput"] input::placeholder {
  color: #B0B0B0;
}

/* Container de Ação (para botões "Sair" ou "Voltar") */
.action-container {
    max-width: 800px; /* Mesma largura do chat-window */
    margin: 1rem auto; /* Centraliza e dá espaço */
    text-align: center; /* Centraliza o botão */
}
</style>
"""
# Aplica o CSS à página
st.markdown(STYLE_CSS, unsafe_allow_html=True)


# --- Gerenciamento de Estado (Telas) ---
# st.session_state é um "dicionário" que persiste enquanto o usuário
# está com a aba do navegador aberta. Usamos ele para:
# 1. 'page': Saber qual tela mostrar (login, chat, etc.)
# 2. 'pontos': Armazenar a pontuação do jogador
# 3. 'character': Guardar o nome do personagem escolhido
# 4. 'messages': Salvar o histórico da conversa do chat

# Inicializa o estado 'page' se ainda não existir
if 'page' not in st.session_state:
    st.session_state.page = 'login'
# Inicializa 'pontos'
if 'pontos' not in st.session_state:
    st.session_state.pontos = 0
# Inicializa 'character'
if 'character' not in st.session_state:
    st.session_state.character = None
# Inicializa 'messages' (histórico do chat)
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- Funções de Navegação ---
# Estas funções simplesmente alteram o valor de 'st.session_state.page'.
# Quando o estado muda, o Streamlit re-executa o script do topo,
# e o "Roteador Principal" (no final do arquivo) mostrará a nova página.

def go_to_character_select():
    """Muda o estado para a página de seleção de personagem."""
    # Como o login é estático, não validamos senha, apenas navegamos
    st.session_state.page = 'character_select'

def go_to_login():
    """Muda o estado para a página de login e reseta o jogo."""
    st.session_state.page = 'login'
    # Reseta os dados do jogo anterior
    st.session_state.pontos = 0
    st.session_state.character = None
    st.session_state.messages = []

def select_character(character_name):
    """Salva o personagem escolhido e navega para a tela do chatbot."""
    st.session_state.character = character_name
    st.session_state.page = 'chatbot'
    # Adiciona uma mensagem de boas-vindas personalizada do bot
    st.session_state.messages = [
        {"role": "assistant", "content": f"Olá! Eu sou {character_name}. Envie a foto de um ponto turístico de Pernambuco e faça uma pergunta sobre ele para ganharmos pontos!"}
    ]

# --- Definição das Telas (Funções) ---
# Cada função é responsável por "desenhar" uma tela específica.

def show_login_page():
    """Renderiza a tela de login customizada (seguindo o design do Figma)."""
    
    # Início do card
    st.markdown("""
    <div class="login-card">
        <h1>Bem-vindo jogador</h1>
        <p>Vamos turistar?</p>
        <div class="input-container">
            <label for="email">E-mail ou nome de usuário</label>
            <input id="email" placeholder="Digite seu e-mail ou nome de usuário" />
        </div>
        <div class="input-container">
            <label for="senha">Senha</label>
            <input type="password" id="senha" placeholder="Digite sua senha" />
        </div>
    """, unsafe_allow_html=True)

    # ✅ Aqui vem o botão funcional do Streamlit (dentro do card)
    entrar = st.button("Entrar", key="botao_login")

    # Se o botão for clicado → vai para a página de personagens
    if entrar:
        go_to_character_select()

    # Rodapé do card (texto + bandeira)
    st.markdown("""
        <p class="footer-text">
            Não possui conta? <a href="#">Cadastre-se</a>
        </p>
        <img class="flag" src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Bandeira_de_Pernambuco.svg/64px-Bandeira_de_Pernambuco.svg.png" alt="Bandeira de Pernambuco" />
    </div>
    """, unsafe_allow_html=True)

    # CSS (mantendo o mesmo estilo visual do botão HTML original)
    st.markdown("""
    <style>
    body, .main {
        background-color: #0E0E0E;
        color: white;
    }
    .login-card {
        background-color: #1E1E1E;
        width: 420px;
        margin: 12vh auto;
        padding: 50px 40px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .login-card h1 {
        font-size: 24px;
        margin-bottom: 5px;
    }
    .login-card p {
        font-size: 15px;
        color: #B0B0B0;
        margin-bottom: 30px;
    }
    .input-container {
        text-align: left;
        margin-bottom: 20px;
    }
    .input-container label {
        display: block;
        font-size: 13px;
        color: #B0B0B0;
        margin-bottom: 5px;
    }
    .input-container input {
        width: 100%;
        padding: 12px;
        border: none;
        border-radius: 8px;
        background-color: #333333;
        color: white;
    }

    /* Botão "Entrar" (st.button) */
    [data-testid="stButton"][key="botao_login"] > button {
        background: linear-gradient(90deg, #4B00E0, #8B5CF6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        width: 100%;
        cursor: pointer;
        transition: opacity 0.3s ease;
        margin-top: 10px;
    }

    [data-testid="stButton"][key="botao_login"] > button:hover {
        opacity: 0.9;
    }

    .footer-text {
        margin-top: 25px;
        font-size: 13px;
        color: #B0B0B0;
    }

    .footer-text a {
        color: #8B5CF6;
        text-decoration: none;
    }

    .footer-text a:hover {
        text-decoration: underline;
    }

    .flag {
        width: 35px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    
    # Fechamos a div do "card"
    st.markdown('</div>', unsafe_allow_html=True)


def show_character_page():
    """Renderiza a tela de seleção de personagem no estilo do Figma."""
    
    st.markdown("""
    <div class="character-page">
        <h1>Escolha seu Personagem</h1>
        <div class="character-grid">
    """, unsafe_allow_html=True)

    # 🔹 João Frevo
    with st.container():
        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            st.markdown("""
            <div class="character-card">
                <h3>João Frevo</h3>
                <img src="assets/joaofrevo.png" alt="João Frevo - personagem pixelado">
            </div>
            """, unsafe_allow_html=True)
            if st.button("Começar", key="joao_frevo"):
                select_character("João do Frevo")

        with col2:
            st.markdown("""
            <div class="character-card">
                <h3>Maria Maracatu</h3>
                <img src="https://i.imgur.com/ndm7v7Y.png" alt="Maria Maracatu - personagem pixelado">
            </div>
            """, unsafe_allow_html=True)
            if st.button("Começar", key="maria_maracatu"):
                select_character("Maria Maracatu")

        with col3:
            st.markdown("""
            <div class="character-card">
                <h3>Capivara Turista</h3>
                <img src="https://i.imgur.com/z7U7lqQ.png" alt="Capivara Turista - personagem pixelado">
            </div>
            """, unsafe_allow_html=True)
            if st.button("Começar", key="capivara_turista"):
                select_character("Capivara Turista")

    st.markdown("""
        </div>
        <div class="back-container">
    """, unsafe_allow_html=True)

    # 🔹 Botão de voltar (funcional)
    if st.button("Voltar ao Login", key="voltar_login"):
        go_to_login()

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 🔹 CSS customizado
    st.markdown("""
    <style>
    body, .main {
        background-color: #0E0E0E;
        color: white;
        font-family: 'Arial', sans-serif;
    }

    .character-page {
        text-align: center;
        margin-top: 5vh;
    }

    .character-page h1 {
        font-size: 28px;
        margin-bottom: 40px;
        font-weight: bold;
    }

    .character-card {
        background-color: #1E1E1E;
        border-radius: 15px;
        padding: 30px 20px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }

    .character-card:hover {
        transform: translateY(-5px);
    }

    .character-card h3 {
        margin-bottom: 20px;
        color: white;
        font-size: 18px;
        text-transform: capitalize;
    }

    .character-card img {
        width: 120px;
        height: 160px;
        object-fit: contain;
        image-rendering: pixelated;
        margin-bottom: 15px;
    }

    [data-testid="stButton"] > button {
        background-color: white;
        color: #1E1E1E;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 0;
        width: 100%;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    [data-testid="stButton"] > button:hover {
        background-color: #e6e6e6;
    }

    .back-container {
        margin-top: 40px;
        text-align: center;
    }

    [data-testid="stButton"][key="voltar_login"] > button {
        background: transparent;
        border: 1px solid #8B5CF6;
        color: #8B5CF6;
        padding: 10px 25px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        width: auto;
    }

    [data-testid="stButton"][key="voltar_login"] > button:hover {
        background-color: #8B5CF6;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


    # --- CSS customizado ---
    st.markdown("""
    <style>
    body, .main {
        background-color: #0E0E0E;
        color: white;
        font-family: 'Arial', sans-serif;
    }

    .character-page {
        text-align: center;
        margin-top: 5vh;
    }

    .character-page h1 {
        font-size: 28px;
        margin-bottom: 40px;
        font-weight: bold;
    }

    .character-grid {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 40px;
        margin-bottom: 50px;
    }

    .character-card {
        background-color: #1E1E1E;
        width: 250px;
        border-radius: 15px;
        padding: 30px 20px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }

    .character-card:hover {
        transform: translateY(-5px);
    }

    .character-card h3 {
        margin-bottom: 20px;
        text-transform: capitalize;
        color: white;
        font-size: 18px;
    }

    .character-card img {
        width: 120px;
        height: 160px;
        object-fit: contain;
        image-rendering: pixelated;
        margin-bottom: 25px;
    }

    .select-btn {
        background-color: white;
        color: #1E1E1E;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 0;
        width: 100%;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    .select-btn:hover {
        background-color: #e6e6e6;
    }

    .back-container {
        text-align: center;
    }

    .back-btn {
        background: transparent;
        border: 1px solid #8B5CF6;
        color: #8B5CF6;
        padding: 10px 25px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .back-btn:hover {
        background-color: #8B5CF6;
        color: white;
    }

    /* Responsividade */
    @media (max-width: 768px) {
        .character-grid {
            flex-direction: column;
            align-items: center;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def show_chatbot_page():
    """Renderiza a página principal do chatbot multimodal (novo design)."""
    
    # Card principal do chat (centralizado e com altura fixa)
    st.markdown('<div class="chat-window">', unsafe_allow_html=True)
    
    # 1. Header com Pontuação
    # Usamos f-string para injetar a pontuação do 'session_state' no HTML
    st.markdown(
        f"""
        <div class="chat-header">
            <span>Pontos: {st.session_state.pontos}</span>
            <img src="https://placehold.co/20x20/FFD700/000000?text=P" alt="[Imagem de moeda]">
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 2. Uploader da Imagem (simulando o '@' do design)
    st.markdown('<div class="uploader-container">', unsafe_allow_html=True)
    # 'st.file_uploader' é o widget de upload de arquivos
    imagem_carregada = st.file_uploader(
        "Envie a imagem do ponto turístico aqui:", 
        type=["jpg", "jpeg", "png"], 
        key="chat_uploader" # Chave única para este widget
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Histórico de Mensagens
    st.markdown('<div class="chat-history-container">', unsafe_allow_html=True)
    
    # Itera sobre a lista 'st.session_state.messages'
    for message in st.session_state.messages:
        # 'st.chat_message' cria o balão de chat (com ícone 'user' ou 'assistant')
        with st.chat_message(message["role"]):
            st.markdown(message["content"]) # Exibe o texto da mensagem
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # 4. Input de Chat (Fixo no rodapé)
    # 'st.chat_input' é um widget que fica fixo no final da tela
    # Ele retorna o texto digitado (o "prompt") quando o usuário aperta Enter
    if prompt := st.chat_input("Faça sua pergunta sobre a imagem..."):
        
        # A. Adiciona a mensagem do usuário ao histórico e à tela
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # B. Verifica se temos os dois inputs necessários (imagem e texto)
        if imagem_carregada is not None and prompt.strip():
            
            # Mostra um "spinner" (loading) enquanto o backend processa
            with st.spinner("Analisando imagem e gerando resposta... 🤖"):
                resposta_bot = "" # Variável para guardar a resposta
                
                if BACKEND_DISPONIVEL:
                    # --- Chamada REAL ao Backend ---
                    try:
                        # Chamamos a função que importamos lá no topo
                        resposta_bot = responder_mensagem(prompt, imagem_carregada)
                        
                        # Lógica de pontos (Exemplo)
                        # TODO: Ajustar esta lógica baseada na resposta real do backend
                        if "correta" in resposta_bot.lower(): 
                            st.session_state.pontos += 10
                            
                    except Exception as e:
                        # Se o backend der erro durante a execução
                        resposta_bot = f"Ocorreu um erro no backend: {e}"
                        
                else:
                    # --- Modo de SIMULAÇÃO (se o backend não foi encontrado) ---
                    time.sleep(2) # Simula o processamento
                    resposta_bot = f"RESPOSTA SIMULADA: A imagem '{imagem_carregada.name}' parece ser... [descrição]... E sobre '{prompt}', a resposta é... [resposta]."
                    st.session_state.pontos += 5 # Simula ganho de pontos

            # C. Adiciona a resposta do bot (real ou simulada) ao histórico e à tela
            st.session_state.messages.append({"role": "assistant", "content": resposta_bot})
            with st.chat_message("assistant"):
                st.markdown(resposta_bot)

        else:
            # Se faltar a imagem ou a pergunta
            resposta_bot = "Por favor, envie uma imagem E uma pergunta para eu poder responder!"
            st.session_state.messages.append({"role": "assistant", "content": resposta_bot})
            with st.chat_message("assistant"):
                st.markdown(resposta_bot)
        
        # Força o script a re-executar.
        # Isso é necessário para atualizar o contador de "Pontos" no Header
        st.experimental_rerun()

    # Fechamento do card principal
    st.markdown('</div>', unsafe_allow_html=True)
    
    # AJUSTE: Botão de sair agora fica em seu próprio container centralizado
    st.markdown('<div class="action-container">', unsafe_allow_html=True)
    st.button("Sair do Quiz", on_click=go_to_login, key="chat_logout")
    st.markdown('</div>', unsafe_allow_html=True)


def show_victory_page():
    """Página placeholder para Vitória."""
    # Reutiliza o estilo do 'chat-window' para manter a consistência
    st.markdown('<div class="chat-window">', unsafe_allow_html=True)
    
    # AJUSTE: Adiciona um container interno para centralizar o conteúdo
    st.markdown('<div style="text-align: center; padding: 4rem 2rem;">', unsafe_allow_html=True)
    st.title("🏆 Vitória! 🏆")
    st.balloons() # Efeito de balões do Streamlit
    st.write(f"Parabéns! Você terminou com {st.session_state.pontos} pontos!")
    st.button("Jogar Novamente", on_click=go_to_login)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def show_defeat_page():
    """Página placeholder para Derrota."""
    # Reutiliza o estilo do 'chat-window'
    st.markdown('<div class="chat-window">', unsafe_allow_html=True)
    
    # AJUSTE: Adiciona um container interno para centralizar o conteúdo
    st.markdown('<div style="text-align: center; padding: 4rem 2rem;">', unsafe_allow_html=True)
    st.title("❄️ Derrota ❄️")
    st.snow() # Efeito de neve do Streamlit
    st.write(f"Fim de jogo. Você fez {st.session_state.pontos} pontos.")
    st.button("Tentar Novamente", on_click=go_to_login)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- Roteador Principal ---
# Este bloco 'if/elif' é o "cérebro" da navegação.
# Ele verifica o valor de 'st.session_state.page' (que nós mudamos
# nas funções de navegação) e decide qual função de tela deve ser executada.

if st.session_state.page == 'login':
    show_login_page()
    
elif st.session_state.page == 'character_select':
    show_character_page()
    
elif st.session_state.page == 'chatbot':
    show_chatbot_page()
    
elif st.session_state.page == 'victory':
    # TODO: Precisamos de uma lógica no 'show_chatbot_page'
    # para navegar para 'victory' (ex: if st.session_state.pontos > 100)
    show_victory_page()
    
elif st.session_state.page == 'defeat':
    # TODO: Precisamos de uma lógica no 'show_chatbot_page'
    # para navegar para 'defeat' (ex: if st.session_state.vidas < 0)
    show_defeat_page()

else:
    # Caso seguro: Se o estado 'page' se corromper, volta ao login
    st.session_state.page = 'login'
    st.experimental_rerun()




