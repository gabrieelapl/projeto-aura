// LOGIN
document.addEventListener("DOMContentLoaded", function () {
  const formLogin = document.getElementById("form-login") || document.querySelector("form.form-login");
  if (!formLogin) return;

  formLogin.addEventListener("submit", function (e) {
    const emailInput = formLogin.querySelector('input[name="email"]');
    const senhaInput = formLogin.querySelector('input[name="senha"]');

    const email = emailInput ? emailInput.value.trim() : "";
    const senha = senhaInput ? senhaInput.value.trim() : "";

    if (!email || !senha) {
      e.preventDefault();
      mostrarErro("Preencha todos os campos.");
      return;
    }

    const emailValido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    if (!emailValido) {
      e.preventDefault();
      mostrarErro("Digite um e-mail válido.");
      return;
    }

    if (senha.length < 4) {
      e.preventDefault();
      mostrarErro("A senha deve ter pelo menos 4 caracteres.");
      return;
    }
  });

  function mostrarErro(mensagem) {
    let erroDiv = formLogin.querySelector(".erro-login");
    if (erroDiv) {
      erroDiv.textContent = message;
    } else {
      erroDiv = document.createElement("div");
      erroDiv.className = "erro-login";
      erroDiv.style.color = "#c0392b";
      erroDiv.style.marginBottom = "15px";
      erroDiv.textContent = mensagem;
      formLogin.prepend(erroDiv);
    }
  }
});

// CADASTRO
document.addEventListener("DOMContentLoaded", function () {
  const formCadastro = document.getElementById("form-cadastro");
  if (!formCadastro) return;

  formCadastro.addEventListener("submit", function (e) {
    const nome = formCadastro.querySelector('input[name="nome"]').value.trim();
    const email = formCadastro.querySelector('input[name="email"]').value.trim();
    const senha = document.getElementById("senha").value.trim();

    const erroExistente = formCadastro.querySelector(".erro-cadastro");
    if (erroExistente) erroExistente.remove();

    let mensagem = "";

    if (!nome || !email || !senha) {
      mensagem = "Preencha todos os campos.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      mensagem = "Digite um e-mail válido.";
    } else if (senha.length < 6) {
      mensagem = "A senha deve ter pelo menos 6 caracteres.";
    }

    if (mensagem) {
      e.preventDefault();
      const div = document.createElement("div");
      div.className = "erro-cadastro";
      div.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          ${mensagem}`;
      formCadastro.insertBefore(div, formCadastro.querySelector("label"));
    }
  });
});

// ALTERAR SENHA
document.addEventListener("DOMContentLoaded", function () {
  const formSenha = document.getElementById("form-senha");
  if (!formSenha) return;

  formSenha.addEventListener("submit", function (e) {
    const atualInput = formSenha.querySelector('input[name="senha_atual"]');
    const novaInput = document.getElementById("nova_senha");
    const confirmarInput = document.getElementById("confirmar_senha");

    if (!atualInput || !novaInput || !confirmarInput) {
      console.warn("Algum campo de alteração de senha não foi encontrado no HTML.");
      return;
    }

    const atual = atualInput.value.trim();
    const nova = novaInput.value.trim();
    const confirmar = confirmarInput.value.trim();

    if (!atual || !nova || !confirmar) {
      e.preventDefault();
      alert("Preencha todos os campos.");
      return;
    }
    if (nova.length < 6) {
      e.preventDefault();
      alert("A nova senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (nova !== confirmar) {
      e.preventDefault();
      alert("As senhas não coincidem.");
    }
  });
});
