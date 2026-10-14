
function openTransactionModal(kind) {
  const modal = document.getElementById('transactionModal');
  const title = document.getElementById('transactionTitle');
  const kindInput = document.getElementById('transactionKind');
  const submit = document.getElementById('transactionSubmit');

  kindInput.value = kind;

  if (kind === 'income') {
    title.textContent = 'Nova receita';
    submit.textContent = 'Salvar receita';
  } else {
    title.textContent = 'Nova despesa';
    submit.textContent = 'Salvar despesa';
  }

  modal.classList.add('is-open');
  document.body.classList.add('modal-open');

  const firstInput = modal.querySelector(
    'input[name="description"]'
  );

  if (firstInput) firstInput.focus();
}
function openBalanceModal() {
    const modal = document.getElementById('balanceModal');

    if (!modal) {
        console.error(
            'Erro: não foi encontrado o elemento #balanceModal no HTML.'
        );
        return;
    }

    modal.classList.add('is-open');
    document.body.classList.add('modal-open');

    const input = modal.querySelector(
        'input[name="target_balance"]'
    );

    if (input) {
        input.focus();
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);

    if (!modal) {
        console.error('Modal não encontrado:', id);
        return;
    }

    modal.classList.remove('is-open');

    if (!document.querySelector('.modal-overlay.is-open')) {
        document.body.classList.remove('modal-open');
    }
}

function closeModalOutside(event, id) {
    if (event.target.id === id) {
        closeModal(id);
    }
}

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        document
            .querySelectorAll('.modal-overlay.is-open')
            .forEach(function (modal) {
                closeModal(modal.id);
            });
    }
});

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.flash').forEach(function (message) {
    window.setTimeout(function () {
      message.style.transition = 'opacity .3s';
      message.style.opacity = '0';

      window.setTimeout(function () {
        message.remove();
      }, 350);
    }, 4500);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const transactionModal = document.getElementById("transactionModal");
  const balanceModal = document.getElementById("balanceModal");

  // Abre a janela de receita ou despesa.
  window.openTransactionModal = function (kind) {
      if (!transactionModal) {
          alert("Não foi encontrada a janela de movimentações no HTML.");
          return;
      }

      const title = document.getElementById("transactionTitle");
      const kindInput = document.getElementById("transactionKind");
      const submitButton = document.getElementById("transactionSubmit");
      const form = transactionModal.querySelector("form");

      const isIncome = kind === "income";

      title.textContent = isIncome ? "Adicionar receita" : "Adicionar despesa";
      kindInput.value = isIncome ? "income" : "expense";
      submitButton.textContent = isIncome ? "Salvar receita" : "Salvar despesa";

      // Limpa os campos ao abrir e coloca a data de hoje.
      form.reset();
      kindInput.value = isIncome ? "income" : "expense";

      const dateInput = form.querySelector('[name="transaction_date"]');
      if (dateInput) {
          dateInput.value = new Date().toLocaleDateString("en-CA");
      }

      showModal(transactionModal);
  };

  // Abre a janela para ajustar o saldo.
  window.openBalanceModal = function () {
      if (!balanceModal) {
          alert("Não foi encontrada a janela de ajuste de saldo no HTML.");
          return;
      }

      showModal(balanceModal);

      const input = balanceModal.querySelector('[name="target_balance"]');
      if (input) {
          input.focus();
      }
  };

  function showModal(modal) {
      modal.classList.add("is-open");
      document.body.classList.add("modal-open");

      const firstInput = modal.querySelector(
          'input:not([type="hidden"]), select'
      );

      if (firstInput) {
          setTimeout(() => firstInput.focus(), 100);
      }
  }

  // Fecha uma janela.
  window.closeModal = function (modalId) {
      const modal = document.getElementById(modalId);

      if (modal) {
          modal.classList.remove("is-open");
      }

      if (!document.querySelector(".modal-overlay.is-open")) {
          document.body.classList.remove("modal-open");
      }
  };

  // Fecha ao clicar fora da janela.
  window.closeModalOutside = function (event, modalId) {
      if (event.target.id === modalId) {
          window.closeModal(modalId);
      }
  };

  // Fecha com a tecla Escape.
  document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
          document.querySelectorAll(".modal-overlay.is-open").forEach((modal) => {
              window.closeModal(modal.id);
          });
      }
  });
});