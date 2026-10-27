# Entrega — Projeto Inicial SMA (PPGCA/UTFPR)

## Conteúdo

| Parte | Arquivo / pasta | Status |
|---|---|---|
| **PP** | [`PP-PEAS.md`](PP-PEAS.md) | Pronto (markdown; gerar PDF depois) |
| **MOD** | [`MOD-Prometheus.md`](MOD-Prometheus.md) | Pronto (markdown + Mermaid) |
| **PRO** | [`../pi-walker/`](../pi-walker/) | Pronto e testado (`--sem-gui`) |

Material de apoio (Aula 7): [`../equipe-software/`](../equipe-software/).

## Como rodar o PRO

No PC Windows (ou qualquer máquina com Python 3.12+):

```bat
cd %USERPROFILE%\mestrado\sma-maspy
.venv\Scripts\activate
pip install maspy-ml pygame
cd pi-walker
python Walker_Main.py --sem-gui
```

Com interface:

```bat
python Walker_Main.py
```

Padrão headless: mapa 10×10, 20% paredes, 4 walkers, alvos de valor **10** e **50**.

**Atenção:** o pacote correto é `maspy-ml`. O `pip install maspy` instala outro projeto e quebra a importação.

## Evidência de execução (exemplo)

```
alvos [(2, 8, 10), (7, 1, 50)] para 4 walkers
...
Walker_4 capturou o alvo 50
Walker_3 capturou o alvo 10
fim da disputa: Walker_4=50, Walker_3=10
```

## PDF para o Moodle

Ainda falta converter **PP + MOD** em **um único PDF** (Word/Google Docs/pandoc) e anexar o código MASPy. Prazo: **30/10/2026 23:59** (horário de Brasília). Envio bloqueado no Moodle até o aluno estar em um grupo.
