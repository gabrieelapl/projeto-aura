const overlay = document.getElementById("pdf-overlay");
const btnVerPdf = document.getElementById("btn-ver-pdf");
const btnFechar = document.getElementById("pdf-fechar");
const viewer = document.getElementById("pdf-viewer");

btnVerPdf.addEventListener("click", () => {
  viewer.src = "{{ url_for('ver_pdf') }}";
  overlay.classList.add("pdf-overlay--ativo");
});

btnFechar.addEventListener("click", () => {
  overlay.classList.remove("pdf-overlay--ativo");
  viewer.src = "";
});

overlay.addEventListener("click", (e) => {
  if (e.target === overlay) {
    overlay.classList.remove("pdf-overlay--ativo");
    viewer.src = "";
  }
});
