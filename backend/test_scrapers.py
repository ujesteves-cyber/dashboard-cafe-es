import asyncio
import json
from main import scrape_conilon_es, scrape_cepea_arabica, scrape_ice_london, scrape_nybot, fetch_ptax

async def test():
    print("--- Conilon ES ---")
    c = await scrape_conilon_es()
    print(f"Preco: R${c['preco']} | Var: {c['variacao']}% | Data: {c['data']}")
    print(f"Tipo: {c['tipo']} | Fonte: {c['fonte']}")
    hist = c.get("historico", [])
    print(f"Historico: {len(hist)} dias")
    for h in hist[:5]:
        print(f"  {h['data']}: R${h['preco']} ({h['variacao']:+.2f}%)")

    print("\n--- Arabica CEPEA ---")
    a = await scrape_cepea_arabica()
    print(f"Preco: R${a['preco']} | Var: {a['variacao']}% | Data: {a['data']}")
    print(f"Historico: {len(a.get('historico', []))} dias")

    print("\n--- ICE London ---")
    i = await scrape_ice_london()
    print(f"Preco: ${i['preco']} | Var: {i['variacao']} | Data: {i['data']}")
    print(f"Tipo: {i['tipo']} | Historico: {len(i.get('historico', []))} dias")

    print("\n--- NYBOT ---")
    n = await scrape_nybot()
    print(f"Preco: {n['preco']}c/lb | Var: {n['variacao']} | Data: {n['data']}")
    print(f"Tipo: {n['tipo']} | Historico: {len(n.get('historico', []))} dias")

    print("\n--- PTAX ---")
    p = await fetch_ptax()
    print(f"Compra: R${p['compra']} | Venda: R${p['venda']}")

asyncio.run(test())
