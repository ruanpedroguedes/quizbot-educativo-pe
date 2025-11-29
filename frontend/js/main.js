function entrar() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (username === "" || password === "") {
        alert("Por favor, preencha nome e senha para continuar!");
        return;
    }

    // Apenas salvando o nome localmente
    localStorage.setItem("username", username);

    // Redireciona para a tela do chatbot
    window.location.href = "chatbot.html";
}
