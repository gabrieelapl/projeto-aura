const btnCopiar = document.getElementById("btn-copiar");
const btnTexto = document.getElementById("btn-copiar-texto");

btnCopiar.addEventListener("click", () => {
  const texto = document.getElementById("resumo-texto");
  if (!texto) return;
  navigator.clipboard.writeText(texto.innerText).then(() => {
    btnTexto.textContent = "Copiado!";
    btnCopiar.classList.add("btn-copiar--copiado");
    setTimeout(() => {
      btnTexto.textContent = "Copiar";
      btnCopiar.classList.remove("btn-copiar--copiado");
    }, 2000);
  });
});

async function gerarResumo() {
  const conteudo = document.getElementById("resumo-conteudo");

  conteudo.innerHTML = `
      <div class="resumo-loading">
        <div class="resumo-loading__spinner"></div>
        <p>Gerando resumo com IA...</p>
      </div>`;

  try {
    const resp = await fetch("/api/resumo", { method: "POST" });
    const data = await resp.json();

    if (data.erro) {
      conteudo.innerHTML = `
          <div class="resumo-erro">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            ${data.erro}
          </div>`;
    } else {
      conteudo.innerHTML = `
          <h2 class="resumo-subtitulo">Resumo</h2>
          <div class="resumo-texto" id="resumo-texto">${data.resumo}</div>`;
    }
  } catch (err) {
    conteudo.innerHTML = `<div class="resumo-erro">Erro ao conectar com o servidor.</div>`;
  }
}

gerarResumo();
