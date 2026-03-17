const BASE = '/api';

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  cotacoes: () => fetchJSON('/cotacoes'),
  historico: () => fetchJSON('/historico'),
  producao: () => fetchJSON('/producao'),
  exportacoes: () => fetchJSON('/exportacoes'),
  analiseIA: () => fetchJSON('/analise-ia'),
  alertas: () => fetchJSON('/alertas'),
  noticias: () => fetchJSON('/noticias'),
  futuros: () => fetchJSON('/futuros'),
  login: (username, password) =>
    fetch(`${BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then((r) => r.json()),
};
