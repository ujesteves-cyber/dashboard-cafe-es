import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Database } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-white/10 rounded-lg p-3 shadow-xl">
      <p className="text-text-secondary text-xs mb-2">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value?.toLocaleString('pt-BR')} mil sacas
        </p>
      ))}
    </div>
  );
};

export default function ProductionChart({ data }) {
  if (!data?.regioes) return null;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-lg font-semibold text-text-primary">
          Produção por Região do ES (mil sacas)
        </h3>
        <Database className="w-4 h-4 text-text-secondary" />
      </div>

      {/* Fonte e safra */}
      <div className="flex items-center gap-3 mb-4 text-xs text-text-secondary">
        {data.safra && <span>Safra: {data.safra}</span>}
        {data.fonte && (
          <>
            <span>·</span>
            <span>{data.fonte}</span>
          </>
        )}
        {data.atualizado_em && (
          <>
            <span>·</span>
            <span>Atualizado: {data.atualizado_em}</span>
          </>
        )}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data.regioes} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="regiao" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
          <Bar dataKey="conilon" name="Conilon" fill="#16a34a" radius={[4, 4, 0, 0]} />
          <Bar dataKey="arabica" name="Arábica" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Total e observação */}
      {data.total_es && (
        <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-4 text-xs text-text-secondary">
          <span>Total ES: <strong className="text-text-primary">{data.total_es.total?.toLocaleString('pt-BR')} mil sacas</strong></span>
          <span>Conilon: {data.total_es.conilon?.toLocaleString('pt-BR')}</span>
          <span>Arábica: {data.total_es.arabica?.toLocaleString('pt-BR')}</span>
        </div>
      )}
      {data.observacao && (
        <p className="mt-2 text-xs text-text-secondary italic">{data.observacao}</p>
      )}
    </div>
  );
}
