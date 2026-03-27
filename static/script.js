function abrirHistorico() {
  document.getElementById('modal-historico').style.display = 'flex';
  document.getElementById('input-telefone').focus();
}

function fecharHistorico() {
  document.getElementById('modal-historico').style.display = 'none';
  novaBusca();
}

function novaBusca() {
  document.getElementById('modal-busca').style.display = 'block';
  document.getElementById('modal-resultado').style.display = 'none';
  document.getElementById('input-telefone').value = '';
  document.getElementById('modal-erro').style.display = 'none';
}

async function buscarAgendamentos() {
  const telefone = document.getElementById('input-telefone').value.trim();
  const erro = document.getElementById('modal-erro');

  if (!telefone) {
    erro.textContent = 'Digite seu número de telefone.';
    erro.style.display = 'block';
    return;
  }

  try {
    const res = await fetch(`/meus-agendamentos?telefone=${encodeURIComponent(telefone)}`);
    const dados = await res.json();

    if (dados.erro) {
      erro.textContent = dados.erro;
      erro.style.display = 'block';
      return;
    }

    erro.style.display = 'none';
    renderizarResultados(dados, telefone);

  } catch (e) {
    erro.textContent = 'Erro ao buscar agendamentos. Tente novamente.';
    erro.style.display = 'block';
  }
}

function renderizarResultados(dados, telefone) {
  document.getElementById('modal-busca').style.display = 'none';
  document.getElementById('modal-resultado').style.display = 'block';

  // Info do cliente (pega do primeiro registro)
  const infoEl = document.getElementById('cliente-info');
  if (dados.length > 0) {
    infoEl.innerHTML = `
      <strong>${dados[0].nome}</strong>
      📱 ${dados[0].telefone}
    `;
  } else {
    infoEl.innerHTML = `📱 ${telefone}`;
  }

  // Lista de agendamentos
  const lista = document.getElementById('lista-agendamentos');

  if (dados.length === 0) {
    lista.innerHTML = `<div class="sem-agendamentos">Nenhum agendamento encontrado.</div>`;
    return;
  }

  const hoje = new Date().toISOString().split('T')[0];

  lista.innerHTML = dados.map(a => {
    const passado = a.data < hoje;
    return `
      <div class="agend-card ${passado ? 'passado' : ''}">
        <div class="agend-servico">${a.servico}</div>
        <div class="agend-detalhe">📅 ${formatarData(a.data)} às ${a.horario}</div>
        <div class="agend-preco">${a.preco}</div>
        <span class="agend-status">${passado ? 'Concluído' : 'Confirmado'}</span>
      </div>
    `;
  }).join('');
}

function formatarData(data) {
  const [ano, mes, dia] = data.split('-');
  return `${dia}/${mes}/${ano}`;
}

// Fecha modal clicando fora
document.getElementById('modal-historico').addEventListener('click', function(e) {
  if (e.target === this) fecharHistorico();
});

// Busca ao pressionar Enter
document.getElementById('input-telefone').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') buscarAgendamentos();
});