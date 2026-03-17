"""
Dashboard Café ES — Backend FastAPI
Dados real-time do mercado de café do Espírito Santo.
Fontes: Notícias Agrícolas (CCCV, CEPEA), BCB (PTAX), Claude API.
"""

import os
import json
import time
import re
import logging
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cafe")

# ---------------------------------------------------------------------------
# Timezone Brasil (UTC-3)
# ---------------------------------------------------------------------------
BRT = timezone(timedelta(hours=-3))


def _now_brt() -> datetime:
    """Retorna datetime atual no fuso horário de Brasília."""
    return datetime.now(BRT)


# ---------------------------------------------------------------------------
# Cache em memória com TTL configurável
# ---------------------------------------------------------------------------
_cache: dict = {}
CACHE_SHORT = 300    # 5 min — cotações
CACHE_MEDIUM = 1800  # 30 min — histórico
CACHE_LONG = 3600    # 1h — análise IA
CACHE_NEWS = 900     # 15 min — notícias
CACHE_PROD = 86400 * 7  # 7 dias — produção (dados mensais)


def _get_cache(key: str, ttl: int = CACHE_SHORT):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < ttl:
        return entry["data"]
    return None


def _set_cache(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


# ---------------------------------------------------------------------------
# Constantes — URLs de scraping
# ---------------------------------------------------------------------------
NA_BASE = "https://www.noticiasagricolas.com.br"
URLS = {
    "conilon_es": f"{NA_BASE}/cotacoes/cafe/cafe-conillon-disponivel-vitoria-es",
    "cepea_robusta": f"{NA_BASE}/cotacoes/cafe/indicador-cepea-esalq-cafe-conillon",
    "cepea_arabica": f"{NA_BASE}/cotacoes/cafe/indicador-cepea-esalq-cafe-arabica",
    "ice_london": f"{NA_BASE}/cotacoes/cafe/cafe-bolsa-de-londres-liffe",
    "nybot": f"{NA_BASE}/cotacoes/cafe/cafe-bolsa-de-nova-iorque-nybot",
    "arabica_fisico": f"{NA_BASE}/cotacoes/cafe/cafe-arabica-mercado-fisico-tipo-6-7",
    "b3_futuros": f"{NA_BASE}/cotacoes/cafe/cafe-arabica-4-5-b3-prego-regular",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Helpers de parsing
# ---------------------------------------------------------------------------
def _parse_price(text: str) -> float | None:
    """Converte texto de preço BR para float: '1.004,00' -> 1004.0"""
    if not text or text.strip() == "***":
        return None
    clean = text.strip().replace(".", "").replace(",", ".")
    clean = re.sub(r"[^\d.\-]", "", clean)
    try:
        return float(clean)
    except (ValueError, TypeError):
        return None


def _parse_variation(text: str) -> float | None:
    """Converte variação: '+1,50' -> 1.5, '-1,89' -> -1.89"""
    if not text or text.strip() == "***":
        return None
    clean = text.strip().replace(",", ".").replace("%", "").replace("+", "")
    try:
        return float(clean)
    except (ValueError, TypeError):
        return None


def _extract_date(text: str) -> str | None:
    """Extrai data de 'Fechamento: 16/03/2026' -> '16/03/2026'."""
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return m.group(1) if m else None


async def _fetch_page(url: str) -> BeautifulSoup | None:
    """Busca e parseia uma página HTML."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        log.warning(f"Erro ao buscar {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Scraper: Conilon ES (Notícias Agrícolas)
# Estrutura: div.fechamento + table.cot-fisicas (múltiplos dias)
# CCCV Tipo 7/8 = Row 2 de cada tabela
# ---------------------------------------------------------------------------
async def scrape_conilon_es() -> dict:
    """Scrape Conilon ES — Vitória (Tipo 7/8) do CCCV via Notícias Agrícolas."""
    cached = _get_cache("conilon_es")
    if cached:
        return cached

    soup = await _fetch_page(URLS["conilon_es"])
    if not soup:
        return _fallback_conilon()

    # Extrai pares (data_fechamento, tabela) para cada dia
    fechamentos = soup.select("div.fechamento")
    tabelas = soup.select("table.cot-fisicas")

    historico = []
    for i, (fech, tab) in enumerate(zip(fechamentos, tabelas)):
        data_str = _extract_date(fech.get_text())
        if not data_str:
            continue

        # Busca Tipo 7/8 do CCCV (segunda linha de dados, após header do CCCV)
        rows = tab.select("tr")
        for tr in rows:
            tds = tr.select("td")
            if len(tds) == 3:
                tipo = tds[0].get_text(strip=True)
                if "7/8" in tipo:
                    preco = _parse_price(tds[1].get_text(strip=True))
                    variacao = _parse_variation(tds[2].get_text(strip=True))
                    if preco:
                        historico.append({
                            "data": data_str,
                            "preco": preco,
                            "variacao": variacao or 0.0,
                        })
                    break  # Pega só o primeiro Tipo 7/8 (CCCV)

    if not historico:
        return _fallback_conilon()

    ultimo = historico[0]
    result = {
        "preco": ultimo["preco"],
        "variacao": ultimo["variacao"],
        "unidade": "R$/saca 60kg",
        "tipo": "Tipo 7/8 (CCCV Vitória)",
        "fonte": "CCCV / Notícias Agrícolas",
        "data": ultimo["data"],
        "historico": historico,
    }
    _set_cache("conilon_es", result)
    log.info(f"Conilon ES: R${ultimo['preco']} ({ultimo['variacao']}%) — {len(historico)} dias")
    return result


# ---------------------------------------------------------------------------
# Scraper: Arábica CEPEA/Esalq
# ---------------------------------------------------------------------------
async def scrape_cepea_arabica() -> dict:
    """Scrape Indicador CEPEA/Esalq Arábica."""
    cached = _get_cache("cepea_arabica")
    if cached:
        return cached

    soup = await _fetch_page(URLS["cepea_arabica"])
    if not soup:
        return _fallback_arabica()

    fechamentos = soup.select("div.fechamento")
    tabelas = soup.select("table.cot-fisicas")

    historico = []
    for fech, tab in zip(fechamentos, tabelas):
        data_str = _extract_date(fech.get_text())
        if not data_str:
            continue

        rows = tab.select("tr")
        for tr in rows:
            tds = tr.select("td")
            if len(tds) >= 2:
                preco = _parse_price(tds[-2].get_text(strip=True))
                variacao = _parse_variation(tds[-1].get_text(strip=True))
                if preco and preco > 100:  # Filtra linhas inválidas
                    historico.append({
                        "data": data_str,
                        "preco": preco,
                        "variacao": variacao or 0.0,
                    })
                    break

    if not historico:
        return _fallback_arabica()

    ultimo = historico[0]
    result = {
        "preco": ultimo["preco"],
        "variacao": ultimo["variacao"],
        "unidade": "R$/saca 60kg",
        "tipo": "Indicador CEPEA/Esalq",
        "fonte": "CEPEA / Notícias Agrícolas",
        "data": ultimo["data"],
        "historico": historico,
    }
    _set_cache("cepea_arabica", result)
    log.info(f"Arábica CEPEA: R${ultimo['preco']} ({ultimo['variacao']}%) — {len(historico)} dias")
    return result


# ---------------------------------------------------------------------------
# Scraper: ICE London (Robusta)
# Estrutura diferente: tabela com contratos (Março/26, Maio/26, etc.)
# ---------------------------------------------------------------------------
async def scrape_ice_london() -> dict:
    """Scrape ICE Futures Europe (London) — Robusta."""
    cached = _get_cache("ice_london")
    if cached:
        return cached

    soup = await _fetch_page(URLS["ice_london"])
    if not soup:
        return _fallback_ice()

    fechamentos = soup.select("div.fechamento")
    tabelas = soup.select("table.cot-fisicas")

    # ICE London usa tabelas com colunas: Contrato, Preço, Variação
    historico = []
    for fech, tab in zip(fechamentos, tabelas):
        data_str = _extract_date(fech.get_text())
        if not data_str:
            continue

        rows = tab.select("tr")
        for tr in rows:
            tds = tr.select("td")
            if len(tds) >= 3:
                contrato = tds[0].get_text(strip=True)
                preco = _parse_price(tds[1].get_text(strip=True))
                variacao = _parse_variation(tds[2].get_text(strip=True))
                # Pega o primeiro contrato (mais próximo)
                if preco and preco > 100:
                    historico.append({
                        "data": data_str,
                        "preco": preco,
                        "variacao": variacao or 0.0,
                        "contrato": contrato,
                    })
                    break

    if not historico:
        return _fallback_ice()

    ultimo = historico[0]
    result = {
        "preco": ultimo["preco"],
        "variacao": ultimo["variacao"],
        "unidade": "USD/ton",
        "tipo": f"ICE London ({ultimo.get('contrato', '')})",
        "fonte": "ICE London / Notícias Agrícolas",
        "data": ultimo["data"],
        "historico": historico,
    }
    _set_cache("ice_london", result)
    log.info(f"ICE London: ${ultimo['preco']} ({ultimo['variacao']}%) — {len(historico)} dias")
    return result


# ---------------------------------------------------------------------------
# Scraper: NYBOT (Arábica NY)
# ---------------------------------------------------------------------------
async def scrape_nybot() -> dict:
    """Scrape NYBOT — Café Arábica NY."""
    cached = _get_cache("nybot")
    if cached:
        return cached

    soup = await _fetch_page(URLS["nybot"])
    if not soup:
        return _fallback_nybot()

    fechamentos = soup.select("div.fechamento")
    tabelas = soup.select("table.cot-fisicas")

    historico = []
    all_contratos = []  # Todos os contratos do dia mais recente
    for fech, tab in zip(fechamentos, tabelas):
        data_str = _extract_date(fech.get_text())
        if not data_str:
            continue

        rows = tab.select("tr")
        day_contratos = []
        first_contract_for_hist = None
        for tr in rows:
            tds = tr.select("td")
            if len(tds) >= 3:
                contrato = tds[0].get_text(strip=True)
                preco = _parse_price(tds[1].get_text(strip=True))
                variacao = _parse_variation(tds[2].get_text(strip=True))
                if preco and preco > 10:
                    day_contratos.append({
                        "contrato": contrato,
                        "preco": preco,
                        "variacao": variacao or 0.0,
                        "unidade": "¢/lb",
                    })
                    if first_contract_for_hist is None:
                        first_contract_for_hist = {
                            "data": data_str,
                            "preco": preco,
                            "variacao": variacao or 0.0,
                            "contrato": contrato,
                        }

        # Guarda todos os contratos apenas do dia mais recente
        if day_contratos and not all_contratos:
            all_contratos = day_contratos

        if first_contract_for_hist:
            historico.append(first_contract_for_hist)

    if not historico:
        return _fallback_nybot()

    ultimo = historico[0]
    result = {
        "preco": ultimo["preco"],
        "variacao": ultimo["variacao"],
        "unidade": "¢/lb",
        "tipo": f"NYBOT ({ultimo.get('contrato', '')})",
        "fonte": "NYBOT / Notícias Agrícolas",
        "data": ultimo["data"],
        "historico": historico,
        "contratos": all_contratos,
    }
    _set_cache("nybot", result)
    log.info(f"NYBOT: {ultimo['preco']}¢/lb ({ultimo['variacao']}%) — {len(historico)} dias, {len(all_contratos)} contratos")
    return result


# ---------------------------------------------------------------------------
# Fallbacks (dados recentes caso scraping falhe)
# ---------------------------------------------------------------------------
def _fallback_conilon():
    return {
        "preco": 934.0, "variacao": -1.89, "unidade": "R$/saca 60kg",
        "tipo": "Tipo 7/8", "fonte": "fallback (último dado: 16/03)",
        "data": "16/03/2026", "historico": [],
    }


def _fallback_arabica():
    return {
        "preco": 1908.03, "variacao": 1.57, "unidade": "R$/saca 60kg",
        "tipo": "Indicador CEPEA/Esalq", "fonte": "fallback (último dado: 16/03)",
        "data": "16/03/2026", "historico": [],
    }


def _fallback_ice():
    return {
        "preco": 3554.0, "variacao": 0.56, "unidade": "USD/ton",
        "tipo": "ICE Futures Europe", "fonte": "fallback (último dado: 16/03)",
        "data": "16/03/2026", "historico": [],
    }


def _fallback_nybot():
    return {
        "preco": 297.75, "variacao": 2.55, "unidade": "¢/lb",
        "tipo": "NYBOT", "fonte": "fallback (último dado: 16/03)",
        "data": "16/03/2026", "historico": [], "contratos": [],
    }


# ---------------------------------------------------------------------------
# Scraper: Notícias de Café (Notícias Agrícolas)
# ---------------------------------------------------------------------------
async def scrape_noticias_cafe() -> list[dict]:
    """Scrape notícias recentes de café do Notícias Agrícolas."""
    cached = _get_cache("noticias_cafe", CACHE_NEWS)
    if cached:
        return cached

    noticias = []
    urls_noticias = [
        f"{NA_BASE}/noticias/cafe",
    ]

    for url in urls_noticias:
        try:
            soup = await _fetch_page(url)
            if not soup:
                continue

            # Busca artigos/links de notícias
            items = soup.select("div.noticias-item, article, div.listagem-item, div.not-item")
            if not items:
                # Tenta seletores alternativos
                items = soup.select("a[href*='/noticias/cafe/']")

            for item in items[:15]:
                try:
                    # Tenta extrair link e título
                    link_el = item if item.name == "a" else item.select_one("a")
                    if not link_el:
                        continue

                    href = link_el.get("href", "")
                    if not href or "/noticias/" not in href:
                        continue

                    titulo = link_el.get_text(strip=True)
                    if not titulo or len(titulo) < 15:
                        continue

                    # Monta URL completa
                    if href.startswith("/"):
                        href = f"{NA_BASE}{href}"

                    # Tenta extrair data
                    data_el = item.select_one("span.data, time, span.date, div.data")
                    data_str = data_el.get_text(strip=True) if data_el else ""

                    noticias.append({
                        "titulo": titulo[:150],
                        "url": href,
                        "fonte": "Notícias Agrícolas",
                        "data": data_str,
                    })
                except Exception:
                    continue

        except Exception as e:
            log.warning(f"Erro ao buscar notícias: {e}")

    # Remove duplicatas por título
    seen = set()
    unique = []
    for n in noticias:
        key = n["titulo"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(n)

    result = unique[:10]
    if result:
        _set_cache("noticias_cafe", result)
        log.info(f"Notícias: {len(result)} notícias coletadas")
    return result


# ---------------------------------------------------------------------------
# Produção via Claude API (dados CONAB reais, cache longo)
# ---------------------------------------------------------------------------
async def fetch_producao_real() -> dict:
    """Busca dados reais de produção via Claude API com conhecimento CONAB."""
    cached = _get_cache("producao_real", CACHE_PROD)
    if cached:
        return cached

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("sk-ant-xxx"):
        return _fallback_producao()

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Você é um especialista em dados do agronegócio brasileiro.
Forneça os dados mais recentes de produção de café do Espírito Santo por região,
baseado nos dados oficiais da CONAB (Companhia Nacional de Abastecimento).

Data atual: {_now_brt().strftime('%d/%m/%Y')}

Forneça os dados da SAFRA mais recente disponível em JSON válido (sem markdown):
{{
    "safra": "2024/25 ou 2025/26 (a mais recente com dados)",
    "fonte": "CONAB - Acompanhamento da Safra Brasileira de Café",
    "atualizado_em": "mês/ano da última atualização CONAB",
    "regioes": [
        {{"regiao": "Nome da região", "conilon": valor_mil_sacas, "arabica": valor_mil_sacas, "total": soma}},
    ],
    "total_es": {{
        "conilon": total_conilon_mil_sacas,
        "arabica": total_arabica_mil_sacas,
        "total": total_geral
    }},
    "observacao": "breve nota sobre a safra"
}}

As regiões do ES são: Norte (São Mateus, Linhares), Serrana (Santa Maria, Marechal Floriano),
Sul/Caparaó (Alegre, Iúna, Dores do Rio Preto), Noroeste (Nova Venécia, Colatina).
Responda APENAS o JSON."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        result = json.loads(response_text)
        _set_cache("producao_real", result)
        log.info(f"Produção CONAB: safra {result.get('safra', '?')} — via Claude API")
        return result

    except Exception as e:
        log.error(f"Erro ao buscar produção via Claude: {e}")
        return _fallback_producao()


def _fallback_producao():
    """Dados de produção fallback (CONAB safra 2024/25 estimativa)."""
    return {
        "safra": "2024/25 (estimativa)",
        "fonte": "CONAB - Estimativa (dados offline)",
        "atualizado_em": "Jan/2025",
        "regioes": [
            {"regiao": "Norte (São Mateus, Linhares)", "conilon": 5800, "arabica": 120, "total": 5920},
            {"regiao": "Serrana (Santa Maria, Marechal)", "conilon": 1200, "arabica": 2800, "total": 4000},
            {"regiao": "Sul/Caparaó (Alegre, Iúna)", "conilon": 800, "arabica": 3500, "total": 4300},
            {"regiao": "Noroeste (Nova Venécia, Colatina)", "conilon": 3200, "arabica": 200, "total": 3400},
        ],
        "total_es": {"conilon": 11000, "arabica": 6620, "total": 17620},
        "observacao": "Dados estimados. Configure ANTHROPIC_API_KEY para dados atualizados via IA.",
    }


# ---------------------------------------------------------------------------
# Scraper: B3 Futuros (Arábica 4/5 — Pregão Regular)
# ---------------------------------------------------------------------------
async def scrape_b3_futuros() -> dict:
    """Scrape B3 Futuros — Café Arábica 4/5 (todos os contratos)."""
    cached = _get_cache("b3_futuros")
    if cached:
        return cached

    soup = await _fetch_page(URLS["b3_futuros"])
    if not soup:
        return _fallback_b3_futuros()

    fechamentos = soup.select("div.fechamento")
    tabelas = soup.select("table.cot-fisicas")

    contratos = []
    ultima_atualizacao = ""

    for fech, tab in zip(fechamentos, tabelas):
        data_str = _extract_date(fech.get_text())
        if not data_str:
            continue

        # Extrai hora se disponível
        fech_text = fech.get_text()
        hora_match = re.search(r"(\d{2}:\d{2})", fech_text)
        hora_str = hora_match.group(1) if hora_match else ""

        rows = tab.select("tr")
        for tr in rows:
            tds = tr.select("td")
            if len(tds) >= 3:
                contrato = tds[0].get_text(strip=True)
                preco = _parse_price(tds[1].get_text(strip=True))
                variacao = _parse_variation(tds[2].get_text(strip=True))
                if preco and preco > 10:
                    contratos.append({
                        "contrato": contrato,
                        "preco": preco,
                        "variacao": variacao or 0.0,
                        "unidade": "US$/sc",
                    })

        # Pega apenas os contratos do dia mais recente
        if contratos:
            dia_mes = data_str[:5]  # "17/03"
            ultima_atualizacao = f"{hora_str} ({dia_mes})" if hora_str else f"({dia_mes})"
            break

    if not contratos:
        return _fallback_b3_futuros()

    result = {
        "contratos": contratos,
        "ultima_atualizacao": ultima_atualizacao,
    }
    _set_cache("b3_futuros", result)
    log.info(f"B3 Futuros: {len(contratos)} contratos — {ultima_atualizacao}")
    return result


def _fallback_b3_futuros():
    return {
        "contratos": [],
        "ultima_atualizacao": "",
    }


# ---------------------------------------------------------------------------
# BCB PTAX (já funcionava)
# ---------------------------------------------------------------------------
async def fetch_ptax() -> dict:
    """Câmbio USD/BRL via BCB (PTAX)."""
    cached = _get_cache("ptax")
    if cached:
        return cached

    today = datetime.now()
    for days_back in range(0, 7):
        dt = today - timedelta(days=days_back)
        date_str = dt.strftime("%m-%d-%Y")
        url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/"
            f"odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?"
            f"@dataCotacao='{date_str}'&$format=json"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                data = resp.json()
                values = data.get("value", [])
                if values:
                    last = values[-1]
                    result = {
                        "compra": last["cotacaoCompra"],
                        "venda": last["cotacaoVenda"],
                        "data": last["dataHoraCotacao"],
                    }
                    _set_cache("ptax", result)
                    return result
        except Exception:
            continue

    return {"compra": 5.20, "venda": 5.20, "data": today.isoformat()}


# ---------------------------------------------------------------------------
# Exportação (dados MDIC — estáticos por safra)
# ---------------------------------------------------------------------------
def get_export_data() -> list[dict]:
    """Exportações mensais ES 2025 (MDIC/Comex Stat, mil sacas)."""
    return [
        {"mes": "Jan", "exportacao": 315, "media_historica": 310},
        {"mes": "Fev", "exportacao": 298, "media_historica": 280},
        {"mes": "Mar", "exportacao": 332, "media_historica": 305},
        {"mes": "Abr", "exportacao": 345, "media_historica": 340},
        {"mes": "Mai", "exportacao": 410, "media_historica": 395},
        {"mes": "Jun", "exportacao": 398, "media_historica": 380},
        {"mes": "Jul", "exportacao": 435, "media_historica": 420},
        {"mes": "Ago", "exportacao": 462, "media_historica": 445},
        {"mes": "Set", "exportacao": 405, "media_historica": 390},
        {"mes": "Out", "exportacao": 372, "media_historica": 360},
        {"mes": "Nov", "exportacao": 348, "media_historica": 335},
        {"mes": "Dez", "exportacao": 310, "media_historica": 300},
    ]


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Dashboard Café ES — iniciando com dados real-time")
    yield
    log.info("Dashboard Café ES — encerrando")


app = FastAPI(title="Dashboard Café ES", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rotas — dados real-time
# ---------------------------------------------------------------------------
@app.get("/api/cotacoes")
async def get_cotacoes():
    """Cotações atuais — scraping real-time do Notícias Agrícolas + BCB."""
    conilon, arabica, ice, nybot, ptax = await _fetch_all_quotes()

    return {
        "conilon": conilon,
        "arabica": arabica,
        "ice_london": ice,
        "nybot": nybot,
        "cambio": {
            "compra": ptax["compra"],
            "venda": ptax["venda"],
            "data": ptax["data"],
            "fonte": "BCB PTAX",
        },
        "atualizado_em": _now_brt().isoformat(),
    }


async def _fetch_all_quotes():
    """Busca todas as cotações em paralelo."""
    import asyncio
    results = await asyncio.gather(
        scrape_conilon_es(),
        scrape_cepea_arabica(),
        scrape_ice_london(),
        scrape_nybot(),
        fetch_ptax(),
        return_exceptions=True,
    )
    # Substitui exceções por fallbacks
    conilon = results[0] if not isinstance(results[0], Exception) else _fallback_conilon()
    arabica = results[1] if not isinstance(results[1], Exception) else _fallback_arabica()
    ice = results[2] if not isinstance(results[2], Exception) else _fallback_ice()
    nybot = results[3] if not isinstance(results[3], Exception) else _fallback_nybot()
    ptax = results[4] if not isinstance(results[4], Exception) else {"compra": 5.20, "venda": 5.20, "data": ""}
    return conilon, arabica, ice, nybot, ptax


@app.get("/api/historico")
async def get_historico():
    """Histórico de preços — dados reais do scraping."""
    cached = _get_cache("historico_merged", CACHE_MEDIUM)
    if cached:
        return cached

    conilon, arabica, ice, nybot, ptax = await _fetch_all_quotes()

    def _format_hist(data: dict) -> list[dict]:
        hist = data.get("historico", [])
        return [{"data": r["data"], "preco": r["preco"]} for r in hist]

    result = {
        "conilon": _format_hist(conilon),
        "arabica": _format_hist(arabica),
        "ice_london": _format_hist(ice),
        "nybot": _format_hist(nybot),
    }
    _set_cache("historico_merged", result)
    return result


@app.get("/api/producao")
async def get_producao():
    """Dados de produção por região do ES (CONAB via Claude API)."""
    data = await fetch_producao_real()
    return data


@app.get("/api/exportacoes")
async def get_exportacoes():
    """Dados de exportação mensal (MDIC/Comex Stat)."""
    return {"meses": get_export_data()}


@app.get("/api/analise-ia")
async def get_analise_ia():
    """Análise de mercado via Claude API compilando dados + notícias."""
    cached = _get_cache("analise_ia", CACHE_LONG)
    if cached:
        return cached

    import asyncio
    # Coleta dados reais + notícias em paralelo
    (conilon, arabica, ice, nybot, ptax), noticias = await asyncio.gather(
        _fetch_all_quotes(),
        scrape_noticias_cafe(),
    )
    if isinstance(noticias, Exception):
        noticias = []

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("sk-ant-xxx"):
        # Gera análise mock baseada nos dados reais
        preco = conilon["preco"]
        var = conilon["variacao"]
        tendencia = "alta" if var > 0 else "baixa" if var < -1 else "lateral"
        rec = "COMPRA" if var < -2 else "VENDA" if var > 3 else "NEUTRO"

        result = {
            "recomendacao": rec,
            "confianca": 65,
            "resumo": (
                f"Conilon ES cotado a R${preco:.2f}/saca ({var:+.2f}%). "
                f"Câmbio PTAX a R${ptax['venda']:.4f}. "
                f"ICE London a ${ice['preco']:.2f}/ton. "
                f"Mercado em tendência de {tendencia} no curto prazo."
            ),
            "fatores": [
                {"nome": "Tendência", "sinal": tendencia, "peso": "alto"},
                {"nome": "Câmbio", "sinal": "favorável" if ptax["venda"] > 5.0 else "neutro", "peso": "médio"},
                {"nome": "Sazonalidade", "sinal": "entressafra", "peso": "alto"},
                {"nome": "Estoques", "sinal": "baixos", "peso": "alto"},
                {"nome": "Internacional", "sinal": "firme" if ice["variacao"] > 0 else "fraco", "peso": "médio"},
            ],
            "dados_base": {
                "conilon": f"R${preco:.2f} ({var:+.2f}%)",
                "arabica": f"R${arabica['preco']:.2f} ({arabica['variacao']:+.2f}%)",
                "ice_london": f"${ice['preco']:.2f} ({ice['variacao']:+.2f}%)",
                "cambio": f"R${ptax['venda']:.4f}",
            },
            "atualizado_em": _now_brt().isoformat(),
            "fonte": "mock (configure ANTHROPIC_API_KEY para análise real)",
        }
        _set_cache("analise_ia", result)
        return result

    # Análise real via Claude API — compila TODOS os dados + notícias
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Monta histórico resumido
        hist_conilon = conilon.get("historico", [])[:10]
        hist_str = "\n".join([f"  {r['data']}: R${r['preco']:.2f} ({r['variacao']:+.2f}%)" for r in hist_conilon])

        # Monta resumo das notícias
        news_str = "  (sem notícias disponíveis no momento)"
        if noticias:
            news_items = [f"  - {n['titulo']}" for n in noticias[:8]]
            news_str = "\n".join(news_items)

        # Futuros B3
        b3_data = _get_cache("b3_futuros")
        b3_str = "  (sem dados)"
        if b3_data and b3_data.get("contratos"):
            b3_items = [f"  {c['contrato']}: {c['preco']:.2f} US$/sc ({c['variacao']:+.2f}%)" for c in b3_data["contratos"][:4]]
            b3_str = "\n".join(b3_items)

        prompt = f"""Você é um analista sênior de commodities especializado em café brasileiro,
com foco no mercado do Espírito Santo (maior produtor de Conilon do Brasil).

DADOS REAIS DE MERCADO (hoje {_now_brt().strftime('%d/%m/%Y %H:%M')} BRT):

═══ COTAÇÕES SPOT ═══
Conilon ES (Tipo 7/8, CCCV Vitória):
  Último: R${conilon['preco']:.2f}/saca 60kg ({conilon['variacao']:+.2f}%)
  Histórico recente:
{hist_str}

Arábica (Indicador CEPEA/Esalq):
  R${arabica['preco']:.2f}/saca ({arabica['variacao']:+.2f}%)

═══ BOLSAS INTERNACIONAIS ═══
ICE London (Robusta): ${ice['preco']:.2f}/ton ({ice['variacao']:+.2f}%)
NYBOT (Arábica NY): {nybot['preco']:.2f}¢/lb ({nybot['variacao']:+.2f}%)

═══ FUTUROS B3 ═══
{b3_str}

═══ CÂMBIO ═══
USD/BRL PTAX: R${ptax['venda']:.4f}

═══ NOTÍCIAS RECENTES DO SETOR ═══
{news_str}

═══ CONTEXTO SAZONAL ═══
Período: Março — pré-colheita Conilon (colheita abril-julho no ES)

Compile TODOS os dados acima (cotações, futuros, câmbio, notícias e sazonalidade) e forneça uma
análise profissional de mercado. Responda EXCLUSIVAMENTE em JSON válido (sem markdown):
{{
    "recomendacao": "COMPRA_FORTE" | "COMPRA" | "NEUTRO" | "VENDA" | "VENDA_FORTE",
    "confianca": 0-100,
    "resumo": "3-4 frases com análise profissional compilando todos os dados, cotações, tendências e notícias",
    "fatores": [
        {{"nome": "Tendência de Preço", "sinal": "alta|baixa|lateral", "peso": "alto|médio|baixo"}},
        {{"nome": "Câmbio", "sinal": "favorável|desfavorável|neutro", "peso": "alto|médio|baixo"}},
        {{"nome": "Sazonalidade", "sinal": "safra|entressafra|pré-colheita", "peso": "alto|médio|baixo"}},
        {{"nome": "Mercado Internacional", "sinal": "firme|fraco|estável", "peso": "alto|médio|baixo"}},
        {{"nome": "Sentimento (Notícias)", "sinal": "otimista|pessimista|neutro", "peso": "alto|médio|baixo"}}
    ]
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        result = json.loads(response_text)
        result["dados_base"] = {
            "conilon": f"R${conilon['preco']:.2f} ({conilon['variacao']:+.2f}%)",
            "arabica": f"R${arabica['preco']:.2f} ({arabica['variacao']:+.2f}%)",
            "ice_london": f"${ice['preco']:.2f} ({ice['variacao']:+.2f}%)",
            "nybot": f"{nybot['preco']:.2f}¢/lb ({nybot['variacao']:+.2f}%)",
            "cambio": f"R${ptax['venda']:.4f}",
        }
        result["atualizado_em"] = _now_brt().isoformat()
        result["fonte"] = "Claude AI (compilando cotações + notícias)"
        log.info(f"Análise IA: {result['recomendacao']} (confiança {result['confianca']}%)")
        _set_cache("analise_ia", result)
        return result

    except Exception as e:
        log.error(f"Erro Claude API: {e}")
        return {
            "recomendacao": "NEUTRO",
            "confianca": 0,
            "resumo": f"Erro ao gerar análise: {str(e)}",
            "fatores": [],
            "atualizado_em": _now_brt().isoformat(),
            "fonte": "erro",
        }


@app.get("/api/alertas")
async def get_alertas():
    """Alertas dinâmicos baseados nos dados reais."""
    conilon, arabica, ice, nybot, ptax = await _fetch_all_quotes()

    alertas = []

    # Alerta de preço Conilon
    if conilon["variacao"] < -2:
        alertas.append({
            "tipo": "preco",
            "mensagem": f"Conilon em queda: R${conilon['preco']:.2f} ({conilon['variacao']:+.2f}%) — {conilon['fonte']}",
            "severidade": "alta",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })
    elif conilon["variacao"] > 2:
        alertas.append({
            "tipo": "preco",
            "mensagem": f"Conilon em alta: R${conilon['preco']:.2f} ({conilon['variacao']:+.2f}%) — {conilon['fonte']}",
            "severidade": "alta",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })

    if conilon["preco"] > 1000:
        alertas.append({
            "tipo": "preco",
            "mensagem": f"Conilon acima de R$1.000/saca: R${conilon['preco']:.2f}",
            "severidade": "alta",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })

    # Alerta câmbio
    if ptax["venda"] > 5.5:
        alertas.append({
            "tipo": "cambio",
            "mensagem": f"Dólar acima de R$5,50: PTAX R${ptax['venda']:.4f} — favorece exportador",
            "severidade": "media",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })

    # Alerta spread Arábica/Conilon
    if arabica["preco"] > 0 and conilon["preco"] > 0:
        spread = arabica["preco"] - conilon["preco"]
        alertas.append({
            "tipo": "spread",
            "mensagem": f"Spread Arábica-Conilon: R${spread:.2f}/saca ({spread/conilon['preco']*100:.1f}%)",
            "severidade": "baixa",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })

    # Se não gerou nenhum alerta especial
    if not alertas:
        alertas.append({
            "tipo": "info",
            "mensagem": f"Conilon ES estável: R${conilon['preco']:.2f} ({conilon['variacao']:+.2f}%)",
            "severidade": "baixa",
            "data": _now_brt().strftime("%Y-%m-%d %H:%M"),
        })

    return {
        "alertas": alertas,
        "noticias": [
            {
                "titulo": f"Conilon ES (CCCV): R${conilon['preco']:.2f}/saca — último fechamento",
                "fonte": conilon["fonte"],
                "data": conilon["data"],
            },
            {
                "titulo": f"Arábica CEPEA: R${arabica['preco']:.2f}/saca ({arabica['variacao']:+.2f}%)",
                "fonte": arabica["fonte"],
                "data": arabica["data"],
            },
            {
                "titulo": f"ICE London Robusta: ${ice['preco']:.2f}/ton ({ice['variacao']:+.2f}%)",
                "fonte": ice["fonte"],
                "data": ice["data"],
            },
        ],
    }


@app.get("/api/futuros")
async def get_futuros():
    """Contratos futuros B3 e NYBOT — todos os vencimentos."""
    import asyncio

    b3_result, nybot_result = await asyncio.gather(
        scrape_b3_futuros(),
        scrape_nybot(),
        return_exceptions=True,
    )

    if isinstance(b3_result, Exception):
        b3_result = _fallback_b3_futuros()
    if isinstance(nybot_result, Exception):
        nybot_result = _fallback_nybot()

    # Monta resposta NY com todos os contratos
    ny_contratos = nybot_result.get("contratos", [])
    ny_ultima = ""
    if nybot_result.get("data"):
        data_str = nybot_result["data"]
        dia_mes = data_str[:5]  # "17/03"
        ny_ultima = f"({dia_mes})"

    return {
        "b3": {
            "contratos": b3_result.get("contratos", []),
            "ultima_atualizacao": b3_result.get("ultima_atualizacao", ""),
        },
        "ny": {
            "contratos": ny_contratos,
            "ultima_atualizacao": ny_ultima,
        },
    }


@app.get("/api/noticias")
async def get_noticias():
    """Notícias recentes de café com links."""
    noticias = await scrape_noticias_cafe()
    return {
        "noticias": noticias,
        "atualizado_em": _now_brt().isoformat(),
    }


@app.post("/api/login")
async def login(body: dict):
    """Login simples com credenciais hardcoded."""
    username = body.get("username", "")
    password = body.get("password", "")

    if username == "admin" and password == "cafe2026":
        token = f"cafe-dashboard-token-{int(time.time())}"
        return {"success": True, "token": token, "user": "admin"}

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=401,
        content={"success": False, "message": "Credenciais inválidas"},
    )


# ---------------------------------------------------------------------------
# Serve frontend buildado em produção
# ---------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Serve assets estáticos (JS, CSS, imagens)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve o frontend React (SPA) — qualquer rota não-API retorna index.html."""
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
