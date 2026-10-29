const inputFoto = document.getElementById("input-foto");
const btnFoto = document.getElementById("btn-mudar-foto");
const preview = document.getElementById("foto-preview");
const avatarSvg = document.querySelector(".editar-avatar svg");
const avatarImg = document.querySelector(
  ".editar-avatar img:not(#foto-preview)",
);

btnFoto.addEventListener("click", () => inputFoto.click());

inputFoto.addEventListener("change", function () {
  const file = this.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.style.display = "block";
    if (avatarSvg) avatarSvg.style.display = "none";
    if (avatarImg) avatarImg.style.display = "none";
  };
  reader.readAsDataURL(file);
});

document.getElementById("form-editar").addEventListener("submit", function (e) {
  const nome = document.querySelector('input[name="nome"]').value.trim();
  if (!nome) {
    e.preventDefault();
    alert("O nome de usuário não pode estar vazio.");
  }
});
