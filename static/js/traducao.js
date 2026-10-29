const btnCopiar = document.getElementById("btn-copiar");
const btnTexto = document.getElementById("btn-copiar-texto");

btnCopiar.addEventListener("click", () => {
  const texto = document.getElementById("traducao-resultado").innerText;
  if (!texto || texto === "A tradução aparecerá aqui...") return;
  navigator.clipboard.writeText(texto).then(() => {
    btnTexto.textContent = "Copiado!";
    btnCopiar.classList.add("btn-copiar--copiado");
    setTimeout(() => {
      btnTexto.textContent = "Copiar";
      btnCopiar.classList.remove("btn-copiar--copiado");
    }, 2000);
  });
});

document.getElementById("btn-traduzir").addEventListener("click", async () => {
  const texto = document.getElementById("texto-original").value.trim();
  const resultado = document.getElementById("traducao-resultado");
  const btn = document.getElementById("btn-traduzir");

  if (!texto) {
    resultado.innerHTML =
      '<span style="color:#c0392b;">Cole um texto no campo ao lado.</span>';
    return;
  }

  btn.disabled = true;
  btn.textContent = "Traduzindo...";
  resultado.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; gap:1rem; padding:2rem 0; color:#aaa;">
        <div class="traducao-spinner"></div>
        <span style="font-family:'Tommy-Light'; font-size:0.88rem;">Processando com IA...</span>
      </div>`;

  try {
    const resp = await fetch("/api/traduzir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });

    const data = await resp.json();

    if (data.erro) {
      resultado.innerHTML = `<span style="color:#c0392b;">⚠ ${data.erro}</span>`;
    } else {
      resultado.textContent = data.traducao;
    }
  } catch (err) {
    resultado.innerHTML =
      '<span style="color:#c0392b;">Erro ao conectar com o servidor.</span>';
  } finally {
    btn.disabled = false;
    btn.textContent = "Traduzir";
  }
});
