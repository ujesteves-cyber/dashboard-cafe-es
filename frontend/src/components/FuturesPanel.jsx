import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

export default function FuturesPanel({ data }) {
  if (!data) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <FuturesColumn
        titulo="Café B3"
        contratos={data.b3?.contratos}
        ultimaAtualizacao={data.b3?.ultima_atualizacao}
        unidadePadrao="US$/sc"
      />
      <FuturesColumn
        titulo="Café NY"
        contratos={data.ny?.contratos}
        ultimaAtualizacao={data.ny?.ultima_atualizacao}
        unidadePadrao="¢/lb"
      />
    </div>
  );
}

function FuturesColumn({ titulo, contratos, ultimaAtualizacao, unidadePadrao }) {
  return (
    <div className="bg-bg-card rounded-xl border border-white/5 p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-accent" />
        <h3 className="text-sm font-semibold text-text-primary">{titulo}</h3>
      </div>

      {/* Table header */}
      <div className="grid grid-cols-3 gap-2 text-xs text-text-secondary font-medium mb-2 px-2">
        <span>CONTRATO</span>
        <span className="text-right">PREÇO</span>
        <span className="text-right">VAR (%)</span>
      </div>

      {/* Rows */}
      <div className="space-y-1">
        {contratos && contratos.length > 0 ? (
          contratos.map((c, i) => (
            <div
              key={i}
              className="grid grid-cols-3 gap-2 px-2 py-2 rounded-lg hover:bg-bg-card-hover transition-colors text-sm"
            >
              <span className="text-text-primary font-medium">{c.contrato}</span>
              <span className="text-right text-text-primary">
                {typeof c.preco === 'number' ? c.preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : c.preco}
                <span className="text-text-secondary text-xs ml-1">{c.unidade || unidadePadrao}</span>
              </span>
              <span className={`text-right flex items-center justify-end gap-1 ${
                c.variacao > 0 ? 'text-positive' : c.variacao < 0 ? 'text-negative' : 'text-text-secondary'
              }`}>
                {c.variacao > 0 ? (
                  <TrendingUp className="w-3.5 h-3.5" />
                ) : c.variacao < 0 ? (
                  <TrendingDown className="w-3.5 h-3.5" />
                ) : null}
                {c.variacao > 0 ? '+' : ''}{typeof c.variacao === 'number' ? c.variacao.toFixed(2) : c.variacao}%
              </span>
            </div>
          ))
        ) : (
          <p className="text-text-secondary text-xs text-center py-4">Sem dados disponíveis</p>
        )}
      </div>

      {/* Timestamp */}
      {ultimaAtualizacao && (
        <p className="text-xs text-text-secondary mt-4 pt-3 border-t border-white/5">
          Última atualização: {ultimaAtualizacao}
        </p>
      )}
    </div>
  );
}
