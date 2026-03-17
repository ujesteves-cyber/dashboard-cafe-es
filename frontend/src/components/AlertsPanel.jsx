import { AlertTriangle, Newspaper, TrendingUp, DollarSign, Cloud } from 'lucide-react';

const SEVERITY_STYLES = {
  alta: 'border-l-negative bg-negative/5',
  media: 'border-l-accent bg-accent/5',
  baixa: 'border-l-blue-500 bg-blue-500/5',
};

const TIPO_ICONS = {
  preco: TrendingUp,
  cambio: DollarSign,
  clima: Cloud,
};

export default function AlertsPanel({ data }) {
  if (!data) return null;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-accent" />
        Alertas & Notícias
      </h3>

      {/* Alertas */}
      <div className="space-y-2 mb-5">
        {data.alertas?.map((alerta, i) => {
          const Icon = TIPO_ICONS[alerta.tipo] || AlertTriangle;
          return (
            <div
              key={i}
              className={`border-l-4 rounded-r-lg px-3 py-2 ${SEVERITY_STYLES[alerta.severidade] || ''}`}
            >
              <div className="flex items-start gap-2">
                <Icon className="w-4 h-4 mt-0.5 text-text-secondary shrink-0" />
                <div>
                  <p className="text-sm text-text-primary">{alerta.mensagem}</p>
                  <p className="text-xs text-text-secondary mt-0.5">{alerta.data}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Notícias */}
      <h4 className="text-sm font-semibold text-text-secondary mb-3 flex items-center gap-2">
        <Newspaper className="w-4 h-4" />
        Notícias Recentes
      </h4>
      <div className="space-y-3">
        {data.noticias?.map((noticia, i) => (
          <div key={i} className="border-b border-white/5 pb-2 last:border-0">
            <p className="text-sm text-text-primary">{noticia.titulo}</p>
            <p className="text-xs text-text-secondary mt-1">
              {noticia.fonte} · {noticia.data}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
