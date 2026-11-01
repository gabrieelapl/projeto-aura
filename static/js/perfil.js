const modalExcluir = document.getElementById("modal-excluir");
const btnExcluir = document.getElementById("btn-excluir");
const btnCancelarE = document.getElementById("btn-cancelar-excluir");

btnExcluir.addEventListener("click", () =>
  modalExcluir.classList.add("modal-overlay--ativo"),
);
btnCancelarE.addEventListener("click", () =>
  modalExcluir.classList.remove("modal-overlay--ativo"),
);
modalExcluir.addEventListener("click", (e) => {
  if (e.target === modalExcluir)
    modalExcluir.classList.remove("modal-overlay--ativo");
});
