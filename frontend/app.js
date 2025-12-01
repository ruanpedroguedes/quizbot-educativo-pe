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

let rounds = 0;
const maxRounds = 10;
let waitingPhoto = false;
let score = 0; 

// --------------------------
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

async function postForm(endpoint, formData) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

// --------------------------
function checkEndGame() {
  if (score >= 3) {
    addMessage("bot", `🎉 Parabéns! Você atingiu ${score} pontos e concluiu o quiz!`);
    questionBox.style.display = "none";
    waitingPhoto = false;
    return true;
  }

  if (rounds >= maxRounds) {
    addMessage("bot", `🏁 Fim do quiz! Você fez ${score} pontos!`);
    questionBox.style.display = "none";
    waitingPhoto = false;
    return true;
  }

  return false;
}

// --------------------------
function updateQuestion(data) {
  console.log("API Response:", data);

  if (data.place_data) {
    waitingPhoto = false;
    questionBox.style.display = "block";
    questionText.style.display = "block";
    questionText.textContent = data.place_data.pergunta ?? "";

    if (data.place_data.imagem) {
      questionImgEl.src = data.place_data.imagem;
      questionImage.style.display = "block";
    } else {
      questionImage.style.display = "none";
    }
  }

  // Quando acertar a foto — passa para nova rodada
  if (data.correct === true && data.points_earned === 1) {
    score++; // <-- Soma corretamente
    scoreEl.textContent = `Pontuação: ${score}`;

    rounds++;

    if (checkEndGame()) return;

    setTimeout(() => {
      const fd = new FormData();
      fd.append("user_id", getUserId());
      postForm("/start-quiz", fd).then(updateQuestion);
    }, 1500);
  }
}

// --------------------------
btnStart.onclick = async () => {
  const userId = getUserId();
  if (!userId) return alert("Digite seu user_id!");

  rounds = 0;
  score = 0;
  scoreEl.textContent = `Pontuação: ${score}`;
  waitingPhoto = false;

  // 📌 Mensagem de boas-vindas antes do quiz iniciar
  addMessage(
    "bot",
    "Olá Jogador!!! Bem vindo ao Quizbot PE 😁\nAqui neste Quiz você irá aprender sobre nossa terrinha Pernambuco/Recife com algumas perguntinhas simples pra você ficar mais sabido 😎👍!"
  );

  const fd = new FormData();
  fd.append("user_id", userId);

  const data = await postForm("/start-quiz", fd);
  setTimeout(() => { // cria uma pausa para não misturar com a mensagem
    addMessage("bot", data.message);
    updateQuestion(data);
  }, 1000);
};


// --------------------------
btnSend.onclick = async () => {
  const userId = getUserId();
  const answer = textInput.value.trim();
  if (!answer) return;

  addMessage("user", answer);

  const fd = new FormData();
  fd.append("user_id", userId);
  fd.append("text_answer", answer);

  const data = await postForm("/answer", fd);
  addMessage("bot", data.message);

  if (data.correct === true) waitingPhoto = true;

  updateQuestion(data);
  textInput.value = "";
};

// --------------------------
btnUpload.onclick = async () => {
  if (!waitingPhoto) {
    addMessage("bot", "📌 Primeiro acerte a pergunta!");
    return;
  }

  const file = imageInput.files[0];
  if (!file) return alert("Selecione uma imagem!");

  const fd = new FormData();
  fd.append("user_id", getUserId());
  fd.append("image", file);

  const data = await postForm("/upload", fd);
  addMessage("bot", data.message);
  updateQuestion(data);
};

// -------------------------

btnClear.onclick = () => {
  messages.innerHTML = "";
  questionBox.style.display = "none";
};
