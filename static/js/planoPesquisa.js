let etapaAtual = 1;
const totalEtapas = 4;
let planoIA = null; 

function atualizarProgresso() {
  const pct = Math.min(100, (etapaAtual / totalEtapas) * 100);
  document.getElementById("barra-fill").style.width = pct + "%";

  if (etapaAtual <= totalEtapas) {
    document.getElementById("label-etapa").textContent =
      `Etapa ${etapaAtual} de ${totalEtapas}`;
  } else {
    document.getElementById("label-etapa").textContent = "Plano gerado!";
  }
}

function mostrarEtapa(n) {
  document
    .querySelectorAll(".plano-etapa-wrap")
    .forEach((el) => el.classList.add("hidden"));
  document.getElementById("plano-nav").classList.add("hidden");
  document.getElementById("nav-salvar").classList.add("hidden");

  if (n <= totalEtapas) {
    document.getElementById(`etapa-${n}`).classList.remove("hidden");
    document.getElementById("plano-nav").classList.remove("hidden");
  } else {
    gerarResultado();
    document.getElementById("etapa-resultado").classList.remove("hidden");
    document.getElementById("nav-salvar").classList.remove("hidden");
    carregarIA();
  }

  atualizarProgresso();
}

function getChecked(etapaId) {
  return Array.from(
    document.querySelectorAll(`#${etapaId} input[type="checkbox"]:checked`),
  ).map((cb) => cb.nextElementSibling.textContent.trim());
}

function preencherLista(ulId, itens) {
  const ul = document.getElementById(ulId);
  ul.innerHTML = "";
  itens.forEach((texto) => {
    const li = document.createElement("li");
    li.textContent = texto;
    ul.appendChild(li);
  });
}

function gerarResultado() {
  const pergunta =
    document.getElementById("pergunta-input").value.trim() ||
    "Nenhuma pergunta informada.";
  document.getElementById("res-pergunta").textContent = pergunta;

  preencherLista("res-inclusao", getChecked("etapa-2"));
  preencherLista("res-exclusao", getChecked("etapa-3"));
  preencherLista("res-banco", getChecked("etapa-4"));
}

// parte da IA
const resIA = document.getElementById("res-ia");
const btnBaixar = document.getElementById("btn-baixar");

function criarSecao(titulo) {
  const secao = document.createElement("div");
  secao.className = "resultado-secao";
  const h2 = document.createElement("h2");
  h2.className = "resultado-secao__titulo";
  h2.textContent = titulo;
  secao.appendChild(h2);
  return secao;
}

function mostrarStatusIA(mensagem, erro) {
  resIA.innerHTML = "";
  const secao = document.createElement("div");
  secao.className = "resultado-secao resultado-secao--last";
  const box = document.createElement("div");
  box.className = "ia-status" + (erro ? " ia-status--erro" : "");

  if (erro) {
    const p = document.createElement("p");
    p.textContent = mensagem;
    const btn = document.createElement("button");
    btn.className = "ia-retry";
    btn.textContent = "Tentar novamente";
    btn.addEventListener("click", carregarIA);
    box.append(p, btn);
  } else {
    box.innerHTML = '<div class="ia-spinner"></div>';
    const p = document.createElement("p");
    p.textContent = mensagem;
    box.appendChild(p);
  }
  secao.appendChild(box);
  resIA.appendChild(secao);
}

function renderizarIA(plano) {
  resIA.innerHTML = "";
  const secoes = [];

  // Pergunta refinada
  let s = criarSecao("Pergunta refinada (sugestão da IA)");
  let p = document.createElement("p");
  p.className = "resultado-secao__texto";
  p.textContent = plano.pergunta_refinada;
  s.appendChild(p);
  secoes.push(s);

  s = criarSecao("Estrutura PICO");
  let ul = document.createElement("ul");
  ul.className = "resultado-lista";
  [
    ["População", plano.pico.populacao],
    ["Intervenção", plano.pico.intervencao],
    ["Comparação", plano.pico.comparacao],
    ["Resultado (desfecho)", plano.pico.desfecho],
  ].forEach(([rotulo, valor]) => {
    const li = document.createElement("li");
    li.textContent = `${rotulo}: ${valor}`;
    ul.appendChild(li);
  });
  s.appendChild(ul);
  secoes.push(s);

  s = criarSecao("Palavras-chave");
  ul = document.createElement("ul");
  ul.className = "resultado-lista";
  [
    ["Português", plano.palavras_chave.portugues],
    ["Inglês", plano.palavras_chave.ingles],
  ].forEach(([rotulo, termos]) => {
    if (!termos.length) return;
    const li = document.createElement("li");
    li.textContent = `${rotulo}: ${termos.join("; ")}`;
    ul.appendChild(li);
  });
  s.appendChild(ul);
  secoes.push(s);

  if (plano.strings_busca.length) {
    s = criarSecao("Strings de busca");
    plano.strings_busca.forEach((item) => {
      const banco = document.createElement("p");
      banco.className = "resultado-busca__banco";
      banco.textContent = item.banco;
      const pre = document.createElement("pre");
      pre.className = "resultado-codigo";
      pre.textContent = item.string;
      s.append(banco, pre);
    });
    const nota = document.createElement("p");
    nota.className = "resultado-nota";
    nota.textContent =
      "Sugestão: teste cada string na própria base e ajuste a sintaxe antes de usar. Os filtros de idioma, tipo de publicação e período devem ser aplicados na interface de cada base.";
    s.appendChild(nota);
    secoes.push(s);
  }

  secoes[secoes.length - 1].classList.add("resultado-secao--last");
  secoes.forEach((sec) => resIA.appendChild(sec));
}

async function carregarIA() {
  planoIA = null;
  btnBaixar.disabled = true;
  mostrarStatusIA("Gerando pergunta refinada e strings de busca...", false);

  const payload = {
    pergunta: document.getElementById("pergunta-input").value.trim(),
    inclusao: getChecked("etapa-2"),
    exclusao: getChecked("etapa-3"),
    bancos: getChecked("etapa-4"),
  };

  try {
    const resp = await fetch("/api/plano-pesquisa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok || data.erro) {
      mostrarStatusIA(data.erro || "Não foi possível gerar o plano.", true);
      btnBaixar.disabled = false; // ainda dá para baixar o que foi escolhido
      return;
    }
    planoIA = data.plano;
    renderizarIA(planoIA);
  } catch (e) {
    mostrarStatusIA("Falha de conexão com o servidor. Tente novamente.", true);
  }
  btnBaixar.disabled = false;
}

document.getElementById("btn-continuar").addEventListener("click", () => {
  if (etapaAtual === 1) {
    const pergunta = document.getElementById("pergunta-input").value;
    if (pergunta.trim().length < 10) {
      document.getElementById("erro-pergunta").classList.remove("hidden");
      return;
    }
    document.getElementById("erro-pergunta").classList.add("hidden");
  }
  etapaAtual++;
  mostrarEtapa(etapaAtual);
});

document.getElementById("pergunta-input").addEventListener("input", () => {
  document.getElementById("erro-pergunta").classList.add("hidden");
});

document.getElementById("btn-salvar").addEventListener("click", () => {
  alert("Plano salvo com sucesso!");
});

btnBaixar.addEventListener("click", () => {
  const itens = (id) =>
    Array.from(document.querySelectorAll(`#${id} li`))
      .map((l) => "• " + l.textContent)
      .join("\n");

  let texto =
    `PLANO DE PESQUISA\n\n` +
    `Pergunta de pesquisa:\n${document.getElementById("res-pergunta").textContent}\n\n` +
    `Critérios de inclusão:\n${itens("res-inclusao")}\n\n` +
    `Critérios de exclusão:\n${itens("res-exclusao")}\n\n` +
    `Banco de dados:\n${itens("res-banco")}`;

  if (planoIA) {
    const p = planoIA;
    texto +=
      `\n\nPergunta refinada (sugestão da IA):\n${p.pergunta_refinada}` +
      `\n\nEstrutura PICO:\n` +
      `• População: ${p.pico.populacao}\n` +
      `• Intervenção: ${p.pico.intervencao}\n` +
      `• Comparação: ${p.pico.comparacao}\n` +
      `• Resultado (desfecho): ${p.pico.desfecho}` +
      `\n\nPalavras-chave:\n` +
      `• Português: ${p.palavras_chave.portugues.join("; ")}\n` +
      `• Inglês: ${p.palavras_chave.ingles.join("; ")}`;
    if (p.strings_busca.length) {
      texto +=
        `\n\nStrings de busca (teste cada uma na base antes de usar):\n` +
        p.strings_busca.map((b) => `${b.banco}:\n${b.string}`).join("\n\n");
    }
  }

  const blob = new Blob([texto], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "plano_pesquisa.txt";
  a.click();
  URL.revokeObjectURL(url);
});

mostrarEtapa(1);
