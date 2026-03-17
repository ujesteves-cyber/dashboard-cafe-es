import { Newspaper, ExternalLink, Clock } from 'lucide-react';

export default function NewsPanel({ data }) {
  if (!data?.noticias?.length) return null;

  return (
    <div className="bg-bg-card rounded-xl p-5 border border-white/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-blue-400" />
          Notícias do Mercado de Café
        </h3>
        <span className="text-xs text-text-secondary flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Atualização a cada 15 min
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.noticias.map((noticia, i) => (
          <a
            key={i}
            href={noticia.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group block border border-white/5 rounded-lg p-3 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm text-text-primary group-hover:text-blue-400 transition-colors leading-snug line-clamp-2">
                {noticia.titulo}
              </p>
              <ExternalLink className="w-3.5 h-3.5 text-text-secondary shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-text-secondary">{noticia.fonte}</span>
              {noticia.data && (
                <>
                  <span className="text-xs text-text-secondary">·</span>
                  <span className="text-xs text-text-secondary">{noticia.data}</span>
                </>
              )}
            </div>
          </a>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-white/5 text-center">
        <a
          href="https://www.noticiasagricolas.com.br/noticias/cafe"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors inline-flex items-center gap-1"
        >
          Ver todas as notícias no Notícias Agrícolas
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}
