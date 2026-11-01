const SECOES = [
  ["objetivo", "Objetivo"],
  ["metodologia", "Metodologia"],
  ["amostra", "Amostra"],
  ["resultados", "Resultados"],
  ["limitacoes", "Limitações"],
  ["conclusao", "Conclusão"],
];

const conteudo = document.getElementById("ficha-conteudo");
const btnExportar = document.getElementById("btn-exportar");

function mostrarCarregando() {
  btnExportar.disabled = true;
  conteudo.innerHTML = "";
  const box = document.createElement("div");
  box.className = "ficha-status";
  box.innerHTML =
    '<div class="ficha-spinner"></div><p>Gerando a ficha técnica do artigo...</p>';
  conteudo.appendChild(box);
}

function mostrarErro(mensagem) {
  btnExportar.disabled = true;
  conteudo.innerHTML = "";
  const box = document.createElement("div");
  box.className = "ficha-status ficha-status--erro";
  const p = document.createElement("p");
  p.textContent = mensagem;
  const btn = document.createElement("button");
  btn.className = "ficha-retry";
  btn.textContent = "Tentar novamente";
  btn.addEventListener("click", carregarFicha);
  box.append(p, btn);
  conteudo.appendChild(box);
}

function renderizarFicha(ficha) {
  conteudo.innerHTML = "";
  SECOES.forEach(([chave, titulo], i) => {
    const secao = document.createElement("div");
    secao.className = "ficha-secao";
    if (i === SECOES.length - 1) secao.classList.add("ficha-secao--last");

    const h2 = document.createElement("h2");
    h2.className = "ficha-secao__titulo";
    h2.textContent = titulo;

    const p = document.createElement("p");
    p.className = "ficha-secao__texto";
    p.textContent = ficha[chave] || "Não informado no artigo.";

    secao.append(h2, p);
    conteudo.appendChild(secao);
  });
  btnExportar.disabled = false;
}

async function carregarFicha() {
  mostrarCarregando();
  try {
    const resp = await fetch("/api/ficha-tecnica", { method: "POST" });
    const data = await resp.json();
    if (!resp.ok || data.erro) {
      mostrarErro(data.erro || "Não foi possível gerar a ficha técnica.");
      return;
    }
    renderizarFicha(data.ficha);
  } catch (e) {
    mostrarErro("Falha de conexão com o servidor. Tente novamente.");
  }
}

btnExportar.addEventListener("click", () => {
  const secoes = document.querySelectorAll(".ficha-secao");
  const texto = Array.from(secoes)
    .map((s) => {
      const titulo = s.querySelector(".ficha-secao__titulo").innerText;
      const corpo = s.querySelector(".ficha-secao__texto").innerText;
      return `${titulo}\n${corpo}`;
    })
    .join("\n\n");

  const blob = new Blob([texto], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ficha_tecnica.txt";
  a.click();
  URL.revokeObjectURL(url);
});

carregarFicha();
