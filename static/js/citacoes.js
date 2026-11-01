let dados = null; 
let aviso = "";
let formatoAtual = "vancouver";

const lista = document.getElementById("citacoes-lista");
const btnExportar = document.getElementById("btn-exportar");

function mostrarCarregando() {
  btnExportar.disabled = true;
  lista.innerHTML = "";
  const box = document.createElement("div");
  box.className = "citacoes-status";
  box.innerHTML =
    '<div class="citacoes-spinner"></div><p>Extraindo e formatando as referências do artigo...</p>';
  lista.appendChild(box);
}

function mostrarErro(mensagem) {
  btnExportar.disabled = true;
  lista.innerHTML = "";
  const box = document.createElement("div");
  box.className = "citacoes-status citacoes-status--erro";
  const p = document.createElement("p");
  p.textContent = mensagem;
  const btn = document.createElement("button");
  btn.className = "citacoes-retry";
  btn.textContent = "Tentar novamente";
  btn.addEventListener("click", carregarCitacoes);
  box.append(p, btn);
  lista.appendChild(box);
}

function renderCitacoes(formato) {
  lista.innerHTML = "";

  if (aviso) {
    const p = document.createElement("p");
    p.className = "citacoes-aviso";
    p.textContent = aviso;
    lista.appendChild(p);
  }

  dados[formato].forEach((c) => {
    const item = document.createElement("div");
    item.className = "citacao-item";

    const texto = document.createElement("p");
    texto.className = "citacao-texto";
    texto.innerHTML = c.html;

    const ref = document.createElement("p");
    ref.className = "citacao-ref";
    ref.textContent = c.ref;

    item.append(texto, ref);
    lista.appendChild(item);
  });
}

async function carregarCitacoes() {
  mostrarCarregando();
  try {
    const resp = await fetch("/api/citacoes", { method: "POST" });
    const data = await resp.json();
    if (!resp.ok || data.erro) {
      mostrarErro(data.erro || "Não foi possível gerar as citações.");
      return;
    }
    dados = data.citacoes;
    aviso = data.aviso || "";
    btnExportar.disabled = false;
    renderCitacoes(formatoAtual);
  } catch (e) {
    mostrarErro("Falha de conexão com o servidor. Tente novamente.");
  }
}

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".tab-btn")
      .forEach((b) => b.classList.remove("tab-btn--active"));
    btn.classList.add("tab-btn--active");
    formatoAtual = btn.dataset.formato;
    if (dados) renderCitacoes(formatoAtual);
  });
});

btnExportar.addEventListener("click", () => {
  if (!dados) return;
  const texto = dados[formatoAtual]
    .map((c) => c.texto + "\n" + c.ref)
    .join("\n\n");

  const blob = new Blob([texto], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `citacoes_${formatoAtual.toUpperCase()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
});

carregarCitacoes();
