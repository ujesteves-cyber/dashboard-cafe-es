import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

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

export default function ExportChart({ data }) {
  if (!data?.meses) return null;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Exportações Mensais do ES & Sazonalidade
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data.meses} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="mes" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
          <Area
            type="monotone"
            dataKey="exportacao"
            name="Exportação 2026"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="media_historica"
            name="Média Histórica"
            stroke="#94a3b8"
            fill="#94a3b8"
            fillOpacity={0.05}
            strokeWidth={1}
            strokeDasharray="5 5"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
