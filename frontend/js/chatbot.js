function enviarMensagem() {
    const input = document.getElementById("user-input");
    const mensagem = input.value.trim();
    if (mensagem === "") return;

    const chatBox = document.getElementById("chat-box");

    // Mensagem do usuário
    const userMsg = document.createElement("div");
    userMsg.classList.add("user-message");
    userMsg.innerText = mensagem;
    chatBox.appendChild(userMsg);

    // Resposta fictícia do bot (simulação de IA)
    setTimeout(() => {
        const botMsg = document.createElement("div");
        botMsg.classList.add("bot-message");

        // Pequenas respostas temáticas
        const respostas = [
            "Você sabia que a Revolução Pernambucana de 1817 foi um marco de liberdade no Brasil?",
            "Olinda foi fundada em 1535 — uma das cidades mais antigas do país!",
            "O frevo é Patrimônio Imaterial da Humanidade, reconhecido pela UNESCO!",
            "O Galo da Madrugada é o maior bloco de carnaval do mundo!",
            "Recife foi a primeira cidade do Brasil a ter um observatório astronômico."
        ];

        const resposta = respostas[Math.floor(Math.random() * respostas.length)];
        botMsg.innerText = resposta;
        chatBox.appendChild(botMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 600);

    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
}
