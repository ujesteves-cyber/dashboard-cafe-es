import { Coffee, Lock, User, LogIn } from 'lucide-react';

export default function LoginPage({ onLogin, error, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    onLogin(form.get('username'), form.get('password'));
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-bg-card rounded-xl border border-white/5 p-8 shadow-2xl">
          {/* Coffee icon + Title */}
          <div className="flex flex-col items-center mb-8">
            <div className="p-3 bg-coffee-900 rounded-xl mb-4">
              <Coffee className="w-8 h-8 text-green-400" />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">Dashboard Café ES</h1>
            <p className="text-xs text-text-secondary mt-1">Mercado de café do Espírito Santo</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-negative/10 border border-negative/30 text-negative text-sm text-center">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-text-secondary mb-1.5">Usuário</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                <input
                  name="username"
                  type="text"
                  required
                  placeholder="Seu usuário"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-bg-primary border border-white/10 text-text-primary placeholder:text-text-secondary/50 text-sm focus:outline-none focus:border-coffee-700 focus:ring-1 focus:ring-coffee-700 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-text-secondary mb-1.5">Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                <input
                  name="password"
                  type="password"
                  required
                  placeholder="Sua senha"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-bg-primary border border-white/10 text-text-primary placeholder:text-text-secondary/50 text-sm focus:outline-none focus:border-coffee-700 focus:ring-1 focus:ring-coffee-700 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-coffee-900 hover:bg-coffee-800 text-text-primary font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshSpinner />
                  Entrando...
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Entrar
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-text-secondary mt-6">
          Dashboard Cafe ES &middot; Dados real-time para fins informativos
        </p>
      </div>
    </div>
  );
}

function RefreshSpinner() {
  return (
    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
