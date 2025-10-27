import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.chatbot import responder_mensagem

st.set_page_config(page_title="Chatbot Multimodal 🎮🤖", layout="centered")

st.title("Chatbot Educacional Multimodal 🎓")
st.write("Bem-vindo ao protótipo do jogo educativo com IA!")


imagem = st.file_uploader("Envie uma imagem (ex: objeto, animal, cena):", type=["jpg", "jpeg", "png"])


pergunta = st.text_input("Faça uma pergunta sobre a imagem:")


if st.button("Enviar"):
    if imagem is not None and pergunta.strip():
        resposta = responder_mensagem(pergunta, imagem)
        st.success(f"🤖 Resposta: {resposta}")
    else:
        st.warning("Por favor, envie uma imagem e uma pergunta.")
