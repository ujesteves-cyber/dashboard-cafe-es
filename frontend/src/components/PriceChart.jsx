import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-white/10 rounded-lg p-3 shadow-xl">
      <p className="text-text-secondary text-xs mb-2">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
        </p>
      ))}
    </div>
  );
};

export default function PriceChart({ data }) {
  if (!data) return null;

  const hasData = data.conilon?.length || data.arabica?.length || data.ice_london?.length;
  if (!hasData) {
    return (
      <div className="bg-bg-card rounded-xl p-5 border border-white/5">
        <h3 className="text-lg font-semibold text-text-primary mb-4">
          Evolução de Preços — Dados Reais
        </h3>
        <p className="text-text-secondary text-sm text-center py-12">
          Aguardando dados do histórico...
        </p>
      </div>
    );
  }

  const maxLen = Math.max(
    data.conilon?.length || 0,
    data.arabica?.length || 0,
    data.ice_london?.length || 0,
  );

  // Inverter para exibir do mais antigo ao mais recente
  const conilon = [...(data.conilon || [])].reverse();
  const arabica = [...(data.arabica || [])].reverse();
  const iceLondon = [...(data.ice_london || [])].reverse();

  const merged = [];
  for (let i = 0; i < maxLen; i++) {
    const entry = {
      data: conilon[i]?.data || arabica[i]?.data || iceLondon[i]?.data || '',
    };
    if (conilon[i]) entry['Conilon ES (R$/sc)'] = conilon[i].preco;
    if (arabica[i]) entry['Arábica CEPEA (R$/sc)'] = arabica[i].preco;
    if (iceLondon[i]) entry['ICE London (USD/t)'] = iceLondon[i].preco;
    merged.push(entry);
  }

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Evolução de Preços — Dados Reais
        </h3>
        <span className="text-[10px] text-text-secondary bg-white/5 px-2 py-0.5 rounded">
          Fonte: Notícias Agrícolas
        </span>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={merged} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="data"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            interval={Math.max(0, Math.floor(merged.length / 6))}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            domain={['auto', 'auto']}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Conilon ES (R$/sc)"
            stroke="#16a34a"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#16a34a' }}
            connectNulls
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Arábica CEPEA (R$/sc)"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 2, fill: '#f59e0b' }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="ICE London (USD/t)"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 2, fill: '#3b82f6' }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
