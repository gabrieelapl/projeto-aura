const filtroAtivo = { valor: "tudo" };

document.querySelectorAll(".filtro-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".filtro-btn")
      .forEach((b) => b.classList.remove("filtro-btn--active"));
    btn.classList.add("filtro-btn--active");
    filtroAtivo.valor = btn.dataset.filtro;
    filtrar(filtroAtivo.valor);
  });
});

function filtrar(filtro) {
  document.querySelectorAll(".artigo-item").forEach((item) => {
    if (filtro === "tudo" || item.dataset.status === filtro) {
      item.style.display = "flex";
    } else {
      item.style.display = "none";
    }
  });
}

function toggleDropdown(btn) {
  const wrap = btn.closest(".artigo-item__status-wrap");
  const dropdown = wrap.querySelector(".status-dropdown");
  const aberto = dropdown.classList.contains("status-dropdown--open");

  document
    .querySelectorAll(".status-dropdown--open")
    .forEach((d) => d.classList.remove("status-dropdown--open"));
  if (!aberto) dropdown.classList.add("status-dropdown--open");
}

function mudarStatus(btn, novoStatus) {
  const wrap = btn.closest(".artigo-item__status-wrap");
  const badge = wrap.querySelector(".status-badge");
  const item = btn.closest(".artigo-item");
  const label = {
    incluido: "Incluído",
    excluido: "Excluído",
    pendente: "Pendente",
  };

  badge.className = `status-badge status-badge--${novoStatus}`;
  badge.innerHTML = `${label[novoStatus]} <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>`;
  badge.onclick = function () {
    toggleDropdown(this);
  };

  item.dataset.status = novoStatus;
  wrap
    .querySelector(".status-dropdown")
    .classList.remove("status-dropdown--open");
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".artigo-item__status-wrap")) {
    document
      .querySelectorAll(".status-dropdown--open")
      .forEach((d) => d.classList.remove("status-dropdown--open"));
  }
});

function abrirModal(id) {
  document.getElementById(id).classList.add("modal-overlay--ativo");
}
function fecharModal(id) {
  document.getElementById(id).classList.remove("modal-overlay--ativo");
}
function salvarRenomear() {
  const nome = document.getElementById("input-renomear").value.trim();
  if (nome) document.querySelector(".projeto-titulo").textContent = nome;
  fecharModal("modal-renomear");
}

document.querySelectorAll(".modal-overlay").forEach((overlay) => {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.remove("modal-overlay--ativo");
  });
});

function recalcularContadores() {
  const artigos = document.querySelectorAll(".artigo-item");
  let tudo = 0,
    incluido = 0,
    excluido = 0,
    pendente = 0;

  artigos.forEach((a) => {
    if (a.style.display !== "none" || true) {
      // conta todos
      tudo++;
      const status = a.dataset.status;
      if (status === "incluido") incluido++;
      else if (status === "excluido") excluido++;
      else pendente++;
    }
  });

  document.getElementById("count-tudo").textContent = tudo;
  document.getElementById("count-incluido").textContent = incluido;
  document.getElementById("count-excluido").textContent = excluido;
  document.getElementById("count-pendente").textContent = pendente;
}

recalcularContadores();

function mudarStatus(btn, novoStatus) {
  const wrap = btn.closest(".artigo-item__status-wrap");
  const badge = wrap.querySelector(".status-badge");
  const item = btn.closest(".artigo-item");
  const label = {
    incluido: "Incluído",
    excluido: "Excluído",
    pendente: "Pendente",
  };

  badge.className = `status-badge status-badge--${novoStatus}`;
  badge.innerHTML = `${label[novoStatus]} <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>`;
  badge.onclick = function () {
    toggleDropdown(this);
  };

  item.dataset.status = novoStatus;
  wrap
    .querySelector(".status-dropdown")
    .classList.remove("status-dropdown--open");

  recalcularContadores();
  const artigoIdx = item.dataset.idx;
  const projetoId = "{{ projeto.id }}";

  fetch(`/atualizar-status/${projetoId}/${artigoIdx}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: novoStatus }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (!data.ok) console.error("Erro ao salvar status:", data);
    })
    .catch((err) => console.error("Erro:", err));
}
