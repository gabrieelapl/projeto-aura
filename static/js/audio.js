const btnPlay = document.getElementById("btn-play");
const iconPlay = document.getElementById("icon-play");
const iconPause = document.getElementById("icon-pause");
const progress = document.getElementById("audio-progress");
const tempoAtual = document.getElementById("tempo-atual");
const speedBtns = document.querySelectorAll(".speed-btn");
const audioEl = document.getElementById("audio-element");

function formatTime(s) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

// Gera o áudio ao carregar
async function gerarAudio() {
  btnPlay.disabled = true;
  btnPlay.style.opacity = "0.5";
  document.querySelector(".audio-artigo-titulo").textContent =
    "Gerando áudio com IA...";

  try {
    const resp = await fetch("/api/audio", { method: "POST" });
    const data = await resp.json();

    if (data.erro) {
      document.querySelector(".audio-artigo-titulo").textContent =
        "⚠ " + data.erro;
      return;
    }

    audioEl.src = data.audio_url;
    audioEl.load();
    document.querySelector(".audio-artigo-titulo").textContent =
      '{{ session.get("artigo_nome", "Resumo do artigo") }}';
    btnPlay.disabled = false;
    btnPlay.style.opacity = "1";

    // Atualiza duração
    audioEl.addEventListener("loadedmetadata", () => {
      progress.max = Math.floor(audioEl.duration);
      document.querySelector(".audio-time span:last-child").textContent =
        formatTime(audioEl.duration);
    });
  } catch (err) {
    document.querySelector(".audio-artigo-titulo").textContent =
      "Erro ao conectar com o servidor.";
  }
}

// Play / Pause
btnPlay.addEventListener("click", () => {
  if (audioEl.paused) {
    audioEl.play();
    iconPlay.style.display = "none";
    iconPause.style.display = "block";
    btnPlay.classList.add("btn-play--playing");
  } else {
    audioEl.pause();
    iconPlay.style.display = "block";
    iconPause.style.display = "none";
    btnPlay.classList.remove("btn-play--playing");
  }
});

// Progresso
audioEl.addEventListener("timeupdate", () => {
  progress.value = Math.floor(audioEl.currentTime);
  tempoAtual.textContent = formatTime(audioEl.currentTime);
  const pct = (audioEl.currentTime / audioEl.duration) * 100;
  progress.style.setProperty("--progress", pct + "%");
});

progress.addEventListener("input", () => {
  audioEl.currentTime = progress.value;
});

audioEl.addEventListener("ended", () => {
  iconPlay.style.display = "block";
  iconPause.style.display = "none";
  btnPlay.classList.remove("btn-play--playing");
  progress.value = 0;
  tempoAtual.textContent = "0:00";
});

// Velocidade
speedBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    speedBtns.forEach((b) => b.classList.remove("speed-btn--active"));
    btn.classList.add("speed-btn--active");
    audioEl.playbackRate = parseFloat(btn.dataset.speed);
  });
});

gerarAudio();
