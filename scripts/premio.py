# Busca o prêmio da soja em Paranaguá e grava premio.json
# Fonte principal: Sistema FAEP (tabela CMA). Reserva: Notícias Agrícolas.
import re, json, sys, urllib.request, datetime as dt
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      'Accept-Language': 'pt-BR,pt;q=0.9'}
MES = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}
def baixar(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'replace')
def num(v):
    v = re.sub(r'<[^>]+>|R\$|\s', '', v).replace('+', '').replace('.', '').replace(',', '.')
    return float(v)
def chave(nome):
    m = re.match(r'([A-Za-zçÇ]{3})[a-zçÇ]*\.?\s*/?\s*(\d{2,4})', nome.strip())
    if not m or m.group(1).lower() not in MES: return None
    ano = int(m.group(2)); ano = ano + 2000 if ano < 100 else ano
    return '%d-%02d' % (ano, MES[m.group(1).lower()])

def faep():
    URL = 'https://www.sistemafaep.org.br/cotacoes/'
    s = re.sub(r'<!--.*?-->', '', baixar(URL), flags=re.S)
    def secao(titulo):
        m = re.search(titulo, s, re.I)
        if not m: return None
        t = re.search(r'<table.*?</table>', s[m.end():], re.S)
        resto = s[m.end() + t.end(): m.end() + t.end() + 3000]
        at = re.search(r'Última atualização:\s*(\d{2}/\d{2}/\d{4})', resto)
        datas = re.findall(r'<th>\s*(\d{2}/\d{2})\s*</th>', t.group(0))
        linhas = []
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', t.group(0), re.S):
            tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
            last = re.search(r'class="lastValue"[^>]*>(.*?)</td>', row, re.S)
            if tds and last:
                linhas.append((re.sub(r'<[^>]+>', '', tds[0]).strip(), last.group(1).strip()))
        data = None
        if datas and at:
            d, mth = map(int, datas[-1].split('/')); ya = int(at.group(1)[-4:]); ma = int(at.group(1)[3:5])
            data = '%02d/%02d/%d' % (d, mth, ya if mth <= ma else ya - 1)
        return {'data': data, 'linhas': linhas}
    p = secao(r'Pr[êe]mio Soja Paranagu[áa]-PR\s*\|\s*CMA')
    if not p or not p['linhas']: raise RuntimeError('tabela de prêmio não encontrada na FAEP')
    meses = {}
    for nome, val in p['linhas']:
        k = chave(nome)
        if k:
            try: meses[k] = round(num(val), 1)
            except ValueError: pass
    if not meses: raise RuntimeError('nenhum mês lido na FAEP')
    out = {'fonte_nome': 'FAEP/CMA', 'fonte': URL, 'fechamento': p['data'], 'meses': meses}
    try:
        f = secao(r'Frete Soja p/ Paranagu[áa]\s*\|\s*CMA')
        for nome, val in f['linhas']:
            if nome.lower().startswith('londrina'): out['frete_londrina'] = {'valor': num(val), 'data': f['data'], 'praca': nome}
    except Exception as e: print('frete:', e)
    try:
        d = secao(r'Soja\s*\|\s*DERAL')
        for nome, val in d['linhas']:
            if nome.lower() == 'londrina': out['deral_londrina'] = {'valor': num(val), 'data': d['data']}
    except Exception as e: print('deral:', e)
    return out

def noticias_agricolas():
    URL = 'https://www.noticiasagricolas.com.br/cotacoes/soja/premio-soja-paranagua-pr'
    s = baixar(URL)
    m = re.search(r'Fechamento:\s*(\d{2}/\d{2}/\d{4})', s)
    tb = re.search(r'<tbody[^>]*>(.*?)</tbody>', s[m.end():], re.S)
    meses = {}
    for nome, val in re.findall(r'<tr>\s*<td>\s*([^<]+?)\s*</td>\s*<td>\s*([^<]+?)\s*</td>', tb.group(1)):
        k = chave(nome)
        if k: meses[k] = round(num(val) * 100, 1)  # US$/bu -> centavos/bu
    if not meses: raise RuntimeError('nenhum mês lido no Notícias Agrícolas')
    return {'fonte_nome': 'Notícias Agrícolas', 'fonte': URL, 'fechamento': m.group(1), 'meses': meses}

out = None
for fn in (faep, noticias_agricolas):
    try: out = fn(); break
    except Exception as e: print(fn.__name__, 'falhou:', e)
if not out: sys.exit('nenhuma fonte respondeu')
out['unidade'] = 'centavos US$/bushel'
out['atualizado_em'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
json.dump(out, open('premio.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
