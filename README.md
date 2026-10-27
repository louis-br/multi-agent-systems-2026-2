# multi-agent-systems-2026-2

Projeto Inicial — **Sistemas Multiagentes** (PPGCA/UTFPR, 2026/2).

Walkers competindo por **2 alvos de valores diferentes** em um grid MASPy, com coordenação, memória compartilhada e juízo de captura.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| [`pi-walker/`](pi-walker/) | **PRO** — protótipo MASPy (Walker + Coordenador + Memória + Juiz) |
| [`entrega/`](entrega/) | **PP** (PEAS) e **MOD** (Prometheus) em Markdown |
| [`equipe-software/`](equipe-software/) | Exemplo de comunicação Aula 7 (material de apoio) |

## Como rodar o PRO

```bat
python -m venv .venv
.venv\Scripts\activate
pip install maspy-ml pygame
cd pi-walker
python Walker_Main.py --sem-gui
```

Com GUI: `python Walker_Main.py`.

Pacote correto: **`maspy-ml`** (não use `pip install maspy`).

## Entrega Moodle

- 1 PDF (PP + MOD) + código MASPy
- Prazo: 30/10/2026 23:59 (BRT)

Ver [`entrega/README-entrega.md`](entrega/README-entrega.md).
