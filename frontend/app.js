const API_BASE = "https://quizbot-educativo-pe.onrender.com";

const userIdInput = document.getElementById("userIdInput");
const btnStart = document.getElementById("btnStart");
const btnSend = document.getElementById("btnSend");
const btnSkip = document.getElementById("btnSkip");
const btnLeaderboard = document.getElementById("btnLeaderboard");
const btnProgress = document.getElementById("btnProgress");
const btnClear = document.getElementById("btnClear");
const btnUpload = document.getElementById("btnUpload");

const textInput = document.getElementById("textInput");
const imageInput = document.getElementById("imageInput");

const messages = document.getElementById("messages");
const questionBox = document.getElementById("questionBox");
const questionText = document.getElementById("questionText");
const questionImage = document.getElementById("questionImage");
const questionImgEl = document.getElementById("questionImgEl");
const scoreEl = document.getElementById("score");

// Funções auxiliares
function getUserId() {
  return userIdInput.value.trim();
}

function addMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = role;
  msg.textContent = text;
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}
function updateQuestion(data) {
  console.log("API Response:", data);

  questionBox.style.display = "block";

  // Atualiza pontuação se existir
  if (data.score !== undefined) {
    scoreEl.textContent = `Pontuação: ${data.score}`;
  }

  // Se vier local da API (imagem e texto)
  if (data.place_data) {
    const pergunta = data.place_data.pergunta;
    const imgUrl = data.place_data.imagem;

    if (pergunta) {
      questionText.textContent = pergunta;
      questionText.style.display = "block";
    }

    if (imgUrl) {
      questionImgEl.src = imgUrl; // URL ABSOLUTA — não alterar!
      questionImage.style.display = "block";
    } else {
      questionImage.style.display = "none";
    }

    return; // já atualizamos pergunta e imagem
  }

  // Quando não tiver nova pergunta (só mensagens do sistema)
  if (data.message) {
    questionText.textContent = data.message;
    questionImage.style.display = "none";
  }
}

btnSkip.onclick = async () => {
  const fd = new FormData();
  fd.append("user_id", getUserId());

  try {
    const data = await postForm("/skip-question", fd);
    console.log("Skip response:", data);
    addMessage("bot", data.message ?? "Próxima pergunta!");
    updateQuestion(data);
  } catch (err) {
    console.error("Skip error:", err);
    addMessage("bot", "⚠ Erro ao pular. O backend não deixou!");
  }
};


async function postForm(endpoint, formData) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

// --------------------------------------------------
// Handlers
// --------------------------------------------------

btnStart.onclick = async () => {
  const userId = getUserId();
  if (!userId) return alert("Digite seu user_id!");

  const fd = new FormData();
  fd.append("user_id", userId);

  const data = await postForm("/start-quiz", fd);
  addMessage("bot", data.message);
  updateQuestion(data);
};

btnSend.onclick = async () => {
  const userId = getUserId();
  const answer = textInput.value.trim();
  if (!answer) return;

  const fd = new FormData();
  fd.append("user_id", userId);
  fd.append("text_answer", answer);

  const data = await postForm("/answer", fd);
  addMessage("user", answer);
  addMessage("bot", data.message);
  updateQuestion(data);
  textInput.value = "";
};

btnSkip.onclick = async () => {
  const fd = new FormData();
  fd.append("user_id", getUserId());

  const data = await postForm("/skip-question", fd);
  addMessage("bot", data.message);
  updateQuestion(data);
};

btnUpload.onclick = async () => {
  const file = imageInput.files[0];
  if (!file) return alert("Selecione uma imagem!");

  const fd = new FormData();
  fd.append("user_id", getUserId());
  fd.append("image", file);

  const data = await postForm("/upload", fd);
  addMessage("bot", data.message);
  updateQuestion(data);
};

btnLeaderboard.onclick = async () => {
  const res = await fetch(`${API_BASE}/leaderboard`);
  const data = await res.json();
  addMessage("bot", JSON.stringify(data.leaderboard));
};

btnProgress.onclick = async () => {
  const userId = getUserId();
  const res = await fetch(`${API_BASE}/progress/${userId}`);
  const data = await res.json();
  addMessage("bot", JSON.stringify(data));
};

btnClear.onclick = () => {
  messages.innerHTML = "";i
  questionBox.style.display = "none";
};
