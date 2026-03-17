import { Brain, RefreshCw, Sparkles } from 'lucide-react';

const RECOMENDACOES = {
  VENDA_FORTE: { label: 'Venda Forte', angle: -72, color: '#dc2626' },
  VENDA: { label: 'Venda', angle: -36, color: '#f97316' },
  NEUTRO: { label: 'Neutro', angle: 0, color: '#eab308' },
  COMPRA: { label: 'Compra', angle: 36, color: '#22c55e' },
  COMPRA_FORTE: { label: 'Compra Forte', angle: 72, color: '#16a34a' },
};

function GaugeNeedle({ angle }) {
  return (
    <g transform={`rotate(${angle}, 100, 100)`}>
      <line x1="100" y1="100" x2="100" y2="30" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
      <circle cx="100" cy="100" r="6" fill="#f8fafc" />
    </g>
  );
}

export default function GaugeIA({ analise, onRefresh, loading }) {
  if (!analise) return null;

  const rec = RECOMENDACOES[analise.recomendacao] || RECOMENDACOES.NEUTRO;
  const isClaudeAI = analise.fonte && analise.fonte.toLowerCase().includes('claude');

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Análise IA do Mercado
            </h3>
            <p className="text-xs text-text-secondary flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-400" />
              {isClaudeAI
                ? 'Claude AI compilando cotações, futuros e notícias'
                : 'Análise baseada em dados de mercado'
              }
            </p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors disabled:opacity-50"
          title="Atualizar análise IA"
        >
          <RefreshCw className={`w-4 h-4 text-text-secondary ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Gauge SVG */}
      <div className="flex justify-center mb-4">
        <svg viewBox="0 0 200 130" className="w-56">
          {/* Arco de fundo */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#334155"
            strokeWidth="16"
            strokeLinecap="round"
          />
          {/* Segmentos coloridos */}
          <path d="M 20 100 A 80 80 0 0 1 46.4 43.2" fill="none" stroke="#dc2626" strokeWidth="16" strokeLinecap="round" />
          <path d="M 46.4 43.2 A 80 80 0 0 1 84.6 22.9" fill="none" stroke="#f97316" strokeWidth="16" />
          <path d="M 84.6 22.9 A 80 80 0 0 1 115.4 22.9" fill="none" stroke="#eab308" strokeWidth="16" />
          <path d="M 115.4 22.9 A 80 80 0 0 1 153.6 43.2" fill="none" stroke="#22c55e" strokeWidth="16" />
          <path d="M 153.6 43.2 A 80 80 0 0 1 180 100" fill="none" stroke="#16a34a" strokeWidth="16" strokeLinecap="round" />
          {/* Ponteiro */}
          <GaugeNeedle angle={rec.angle} />
          {/* Labels */}
          <text x="20" y="120" fill="#94a3b8" fontSize="7" textAnchor="start">Venda</text>
          <text x="180" y="120" fill="#94a3b8" fontSize="7" textAnchor="end">Compra</text>
        </svg>
      </div>

      {/* Recomendação */}
      <div className="text-center mb-4">
        <span
          className="text-2xl font-bold px-4 py-1 rounded-full"
          style={{ color: rec.color, backgroundColor: rec.color + '20' }}
        >
          {rec.label}
        </span>
      </div>

      {/* Resumo */}
      <p className="text-text-secondary text-sm leading-relaxed mb-4">
        {analise.resumo}
      </p>

      {/* Fatores */}
      <div className="flex flex-wrap gap-2 mb-3">
        {analise.fatores?.map((f, i) => (
          <span
            key={i}
            className="px-2.5 py-1 rounded-full text-xs font-medium bg-white/5 border border-white/10 text-text-secondary"
          >
            {f.nome}: <span className={
              f.sinal === 'alta' || f.sinal === 'favorável' || f.sinal === 'firme' || f.sinal === 'baixos' || f.sinal === 'otimista'
                ? 'text-positive'
                : f.sinal === 'baixa' || f.sinal === 'desfavorável' || f.sinal === 'fraco' || f.sinal === 'altos' || f.sinal === 'pessimista'
                  ? 'text-negative'
                  : 'text-accent'
            }>{f.sinal}</span>
          </span>
        ))}
      </div>

      {/* Barra de confiança */}
      <div className="mt-3">
        <div className="flex justify-between text-xs text-text-secondary mb-1">
          <span>Confiança da análise</span>
          <span>{analise.confianca}%</span>
        </div>
        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${analise.confianca}%`,
              backgroundColor: analise.confianca > 70 ? '#16a34a' : analise.confianca > 40 ? '#eab308' : '#dc2626',
            }}
          />
        </div>
      </div>

      {/* Timestamp */}
      <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-text-secondary">
        <span className="flex items-center gap-1">
          {isClaudeAI ? (
            <><Sparkles className="w-3 h-3 text-purple-400" /> Claude AI</>
          ) : (
            <><Brain className="w-3 h-3" /> Dados calculados</>
          )}
        </span>
        {analise.atualizado_em && (
          <span>{new Date(analise.atualizado_em).toLocaleString('pt-BR')}</span>
        )}
      </div>
    </div>
  );
}
