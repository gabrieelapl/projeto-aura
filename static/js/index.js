const hamburger = document.getElementById("hamburger");
const navMenu = document.getElementById("nav-menu");
hamburger.addEventListener("click", () => {
  navMenu.classList.toggle("navbar__nav--open");
  hamburger.classList.toggle("navbar__hamburger--active");
});
document.querySelectorAll(".navbar__link").forEach((link) => {
  link.addEventListener("click", () => {
    navMenu.classList.remove("navbar__nav--open");
    hamburger.classList.remove("navbar__hamburger--active");
  });
});

const inputArtigo = document.getElementById("input-artigo");
const btnSelecionar = document.getElementById("btn-selecionar");
const dropzone = document.getElementById("upload-dropzone");
const formUpload = document.getElementById("form-upload");

btnSelecionar.addEventListener("click", (e) => {
  e.stopPropagation();
  inputArtigo.click();
});
dropzone.addEventListener("click", () => inputArtigo.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.style.background = "#7a3fd4";
});
dropzone.addEventListener("dragleave", () => {
  dropzone.style.background = "";
});
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.style.background = "";
  const file = e.dataTransfer.files[0];
  if (file) processarArquivo(file);
});

inputArtigo.addEventListener("change", function () {
  if (this.files[0]) processarArquivo(this.files[0]);
});

function processarArquivo(file) {
  const tam = (file.size / (1024 * 1024)).toFixed(1);

  const dt = new DataTransfer();
  dt.items.add(file);
  document.getElementById("input-artigo-form").files = dt.files;

  document.getElementById("artigo-nome-hidden").value = file.name;
  document.getElementById("artigo-tamanho-hidden").value = `${tam}MB`;
  document.getElementById("file-name").textContent = `${file.name} (${tam}MB)`;

  dropzone.style.display = "none";
  formUpload.style.display = "block";
}

document.getElementById("file-remove").addEventListener("click", () => {
  inputArtigo.value = "";
  formUpload.style.display = "none";
  dropzone.style.display = "flex";
});

document.querySelectorAll('input[name="projeto_radio"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    document
      .querySelectorAll(".upload__option")
      .forEach((o) => o.classList.remove("upload__option--selected"));
    radio.closest(".upload__option").classList.add("upload__option--selected");
    document.getElementById("projeto-tipo-hidden").value = radio.value;
    if (radio.value === "novo") {
      document.getElementById("area-novo-projeto").style.display = "block";
      document.getElementById("area-projeto-existente").style.display = "none";
    } else {
      document.getElementById("area-novo-projeto").style.display = "none";
      document.getElementById("area-projeto-existente").style.display = "block";
    }
  });
});

const selectProjeto = document.getElementById("select-projeto");
if (selectProjeto) {
  selectProjeto.addEventListener("change", () => {
    document.getElementById("projeto-id-hidden").value = selectProjeto.value;
  });
}

function toggleMenu(btn) {
  const wrap = btn.closest(".projeto-card__menu-wrap");
  const dd = wrap.querySelector(".card-dropdown");
  const open = dd.classList.contains("card-dropdown--open");
  document
    .querySelectorAll(".card-dropdown--open")
    .forEach((d) => d.classList.remove("card-dropdown--open"));
  if (!open) dd.classList.add("card-dropdown--open");
}
document.addEventListener("click", (e) => {
  if (!e.target.closest(".projeto-card__menu-wrap"))
    document
      .querySelectorAll(".card-dropdown--open")
      .forEach((d) => d.classList.remove("card-dropdown--open"));
});

function abrirRenomear(id, nome) {
  const novoNome = prompt("Novo nome do projeto:", nome);
  if (novoNome && novoNome.trim()) {
    fetch(`/renomear-projeto/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome: novoNome.trim() }),
    }).then(() => location.reload());
  }
}

function deletarProjeto(id) {
  if (confirm("Deletar este projeto? Esta ação é irreversível.")) {
    fetch(`/deletar-projeto/${id}`, { method: "POST" }).then(() =>
      location.reload(),
    );
  }
}

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        observer.unobserve(e.target);
      }
    });
  },
  { threshold: 0.12 },
);
document
  .querySelectorAll(".projeto-card, .card-sobreAura, .upload__card")
  .forEach((el) => {
    el.classList.add("fade-in");
    observer.observe(el);
  });

window.addEventListener("pageshow", (e) => {
  if (e.persisted) location.reload();
});
