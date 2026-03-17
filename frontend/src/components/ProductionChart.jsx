import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
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

export default function ProductionChart({ data }) {
  if (!data?.regioes) return null;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Produção por Região do ES (mil sacas)
      </h3>
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
    </div>
  );
}
