import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function KpiCard({ titulo, preco, variacao, unidade, fonte, data, icone: Icone }) {
  const isPositive = variacao > 0;
  const isNeutral = variacao === 0;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5 hover:border-coffee-700/50 transition-all duration-300 hover:shadow-lg hover:shadow-coffee-900/20">
      <div className="flex items-center justify-between mb-3">
        <span className="text-text-secondary text-sm font-medium uppercase tracking-wider">
          {titulo}
        </span>
        {Icone && <Icone className="w-5 h-5 text-brown-400" />}
      </div>

      <div className="text-3xl font-bold text-text-primary mb-1">
        {typeof preco === 'number' ? preco.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : preco}
      </div>

      <div className="flex items-center justify-between mb-2">
        <span className="text-text-secondary text-xs">{unidade}</span>
        <div className={`flex items-center gap-1 text-sm font-semibold ${
          isNeutral ? 'text-text-secondary' : isPositive ? 'text-positive' : 'text-negative'
        }`}>
          {isNeutral ? <Minus className="w-4 h-4" /> : isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {isPositive ? '+' : ''}{variacao?.toFixed(2)}%
        </div>
      </div>

      {(fonte || data) && (
        <div className="border-t border-white/5 pt-2 mt-1">
          {fonte && <p className="text-[10px] text-text-secondary truncate">{fonte}</p>}
          {data && <p className="text-[10px] text-text-secondary">{data}</p>}
        </div>
      )}
    </div>
  );
}
