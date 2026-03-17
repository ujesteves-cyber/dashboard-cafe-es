import { useState, useEffect, useCallback } from 'react';
import { Coffee, RefreshCw, Calendar, DollarSign, Globe, BarChart3, LogOut } from 'lucide-react';
import { api } from './api';
import LoginPage from './components/LoginPage';
import KpiCard from './components/KpiCard';
import PriceChart from './components/PriceChart';
import ProductionChart from './components/ProductionChart';
import GaugeIA from './components/GaugeIA';
import AlertsPanel from './components/AlertsPanel';
import ExportChart from './components/ExportChart';
import FuturesPanel from './components/FuturesPanel';

function Header({ ultimaAtualizacao, onRefresh, loading, onLogout }) {
  return (
    <header className="border-b border-white/5 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-coffee-900 rounded-lg">
            <Coffee className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text-primary">
              Dashboard Café — Espírito Santo
            </h1>
            <p className="text-xs text-text-secondary">
              Dados real-time · CCCV · CEPEA · ICE · NYBOT · BCB
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-coffee-900/50 hover:bg-coffee-900 transition-colors disabled:opacity-50 text-xs text-text-primary"
            title="Atualizar dados"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>

          {ultimaAtualizacao && (
            <span className="text-xs text-text-secondary flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(ultimaAtualizacao).toLocaleString('pt-BR')}
            </span>
          )}

          <button
            onClick={onLogout}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-negative/20 hover:bg-negative/40 transition-colors text-xs text-text-primary"
            title="Sair"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginError, setLoginError] = useState(null);
  const [loginLoading, setLoginLoading] = useState(false);

  const [cotacoes, setCotacoes] = useState(null);
  const [historico, setHistorico] = useState(null);
  const [producao, setProducao] = useState(null);
  const [exportacoes, setExportacoes] = useState(null);
  const [analiseIA, setAnaliseIA] = useState(null);
  const [alertas, setAlertas] = useState(null);
  const [futuros, setFuturos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingIA, setLoadingIA] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (username, password) => {
    setLoginLoading(true);
    setLoginError(null);
    try {
      const result = await api.login(username, password);
      if (result.success) {
        setIsLoggedIn(true);
      } else {
        setLoginError(result.message || 'Usuário ou senha inválidos');
      }
    } catch (err) {
      setLoginError('Erro ao conectar ao servidor');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCotacoes(null);
    setHistorico(null);
    setProducao(null);
    setExportacoes(null);
    setAnaliseIA(null);
    setAlertas(null);
    setFuturos(null);
  };

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cot, hist, prod, exp, ia, alt, fut] = await Promise.all([
        api.cotacoes(),
        api.historico(),
        api.producao(),
        api.exportacoes(),
        api.analiseIA(),
        api.alertas(),
        api.futuros(),
      ]);
      setCotacoes(cot);
      setHistorico(hist);
      setProducao(prod);
      setExportacoes(exp);
      setAnaliseIA(ia);
      setAlertas(alt);
      setFuturos(fut);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      fetchAll();
      const interval = setInterval(fetchAll, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [fetchAll, isLoggedIn]);

  const refreshIA = async () => {
    setLoadingIA(true);
    try {
      const ia = await api.analiseIA();
      setAnaliseIA(ia);
    } finally {
      setLoadingIA(false);
    }
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} error={loginError} loading={loginLoading} />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-bg-card rounded-xl p-8 border border-negative/30 max-w-md text-center">
          <p className="text-negative text-lg mb-2">Erro ao carregar dados</p>
          <p className="text-text-secondary text-sm mb-4">{error}</p>
          <p className="text-text-secondary text-xs mb-4">
            Verifique se o backend está rodando: <code className="text-accent">cd backend && python main.py</code>
          </p>
          <button
            onClick={fetchAll}
            className="px-4 py-2 bg-coffee-900 text-white rounded-lg hover:bg-coffee-800 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header
        ultimaAtualizacao={cotacoes?.atualizado_em}
        onRefresh={fetchAll}
        loading={loading}
        onLogout={handleLogout}
      />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Linha 1 — KPI Cards (5 cards) */}
        {loading && !cotacoes ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-bg-card rounded-xl p-5 border border-white/5 animate-pulse h-32" />
            ))}
          </div>
        ) : cotacoes && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <KpiCard
              titulo="Conilon ES"
              preco={cotacoes.conilon?.preco}
              variacao={cotacoes.conilon?.variacao}
              unidade={cotacoes.conilon?.unidade || "R$/saca 60kg"}
              fonte={cotacoes.conilon?.fonte}
              data={cotacoes.conilon?.data}
              icone={Coffee}
            />
            <KpiCard
              titulo="Arábica CEPEA"
              preco={cotacoes.arabica?.preco}
              variacao={cotacoes.arabica?.variacao}
              unidade={cotacoes.arabica?.unidade || "R$/saca 60kg"}
              fonte={cotacoes.arabica?.fonte}
              data={cotacoes.arabica?.data}
              icone={Coffee}
            />
            <KpiCard
              titulo="ICE London"
              preco={cotacoes.ice_london?.preco}
              variacao={cotacoes.ice_london?.variacao}
              unidade={cotacoes.ice_london?.unidade || "USD/ton"}
              fonte={cotacoes.ice_london?.fonte}
              data={cotacoes.ice_london?.data}
              icone={Globe}
            />
            <KpiCard
              titulo="NYBOT NY"
              preco={cotacoes.nybot?.preco}
              variacao={cotacoes.nybot?.variacao}
              unidade={cotacoes.nybot?.unidade || "¢/lb"}
              fonte={cotacoes.nybot?.fonte}
              data={cotacoes.nybot?.data}
              icone={BarChart3}
            />
            <KpiCard
              titulo="Câmbio USD/BRL"
              preco={cotacoes.cambio?.venda}
              variacao={
                cotacoes.cambio?.venda && cotacoes.cambio?.compra
                  ? Math.round((cotacoes.cambio.venda - cotacoes.cambio.compra) / cotacoes.cambio.compra * 10000) / 100
                  : 0
              }
              unidade="PTAX Venda"
              fonte={cotacoes.cambio?.fonte}
              data={cotacoes.cambio?.data}
              icone={DollarSign}
            />
          </div>
        )}

        {/* Linha 2 — Futuros B3 e NY */}
        <FuturesPanel data={futuros} />

        {/* Linha 3 — Gráficos Principais */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PriceChart data={historico} />
          <ProductionChart data={producao} />
        </div>

        {/* Linha 3 — IA + Alertas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GaugeIA analise={analiseIA} onRefresh={refreshIA} loading={loadingIA} />
          <AlertsPanel data={alertas} />
        </div>

        {/* Linha 4 — Exportações */}
        <ExportChart data={exportacoes} />
      </main>

      <footer className="border-t border-white/5 px-6 py-4 mt-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-text-secondary">
          <span>Dashboard Café ES · Dados real-time para fins informativos</span>
          <span>Fontes: CCCV Vitória · CEPEA/Esalq · ICE London · NYBOT · BCB PTAX · CONAB</span>
        </div>
      </footer>
    </div>
  );
}
