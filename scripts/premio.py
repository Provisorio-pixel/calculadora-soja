# Busca o prêmio da soja em Paranaguá (Notícias Agrícolas) e grava premio.json
import re, json, sys, urllib.request, datetime as dt
URL = 'https://www.noticiasagricolas.com.br/cotacoes/soja/premio-soja-paranagua-pr'
MES = {'janeiro':1,'fevereiro':2,'março':3,'marco':3,'abril':4,'maio':5,'junho':6,'julho':7,
       'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
req = urllib.request.Request(URL, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9'})
s = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
m = re.search(r'Fechamento:\s*(\d{2}/\d{2}/\d{4})', s)
if not m: sys.exit('fechamento não encontrado')
tb = re.search(r'<tbody[^>]*>(.*?)</tbody>', s[m.end():], re.S)
if not tb: sys.exit('tabela não encontrada')
meses = {}
for nome, val in re.findall(r'<tr>\s*<td>\s*([^<]+?)\s*</td>\s*<td>\s*([^<]+?)\s*</td>', tb.group(1)):
    mm = re.match(r'([A-Za-zçÇ]+)\s*/\s*(\d{2,4})', nome.strip())
    if not mm or mm.group(1).lower() not in MES: continue
    ano = int(mm.group(2)); ano = ano + 2000 if ano < 100 else ano
    try: c = round(float(val.replace('+', '').replace(',', '.')) * 100, 1)  # US$/bu -> centavos/bu
    except ValueError: continue
    meses['%d-%02d' % (ano, MES[mm.group(1).lower()])] = c
if not meses: sys.exit('nenhum mês lido')
out = {'fechamento': m.group(1), 'fonte': URL, 'unidade': 'centavos US$/bushel',
       'atualizado_em': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'meses': meses}
json.dump(out, open('premio.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out)
