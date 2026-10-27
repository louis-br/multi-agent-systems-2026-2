# MOD — Modelagem Prometheus
## Projeto Inicial — Sistemas Multiagentes (PPGCA/UTFPR)
### Tema: Walkers competindo por alvos de valores diferentes (MASPy)

Este documento apresenta a modelagem no estilo **Prometheus** (visão de agentes, percepções, ações, protocolos e objetivos), alinhada ao protótipo `pi-walker/`. Os diagramas Mermaid podem ser colados no Draw.io / Miro / Mermaid Live.

---

## 1. Visão geral do sistema

```mermaid
flowchart LR
  subgraph Ambiente["Ambiente Map (grid 2D)"]
    Alvos["2 alvos (valores distintos)"]
    Paredes["Paredes"]
    Pos["Posições dos Walkers"]
  end

  C[Coordenador]
  M[Memória]
  J[Juiz]
  W1[Walker_1]
  W2[Walker_2]
  Wn[Walker_N]

  C -->|tell alvos / achieve move / untell| W1
  C -->|tell alvos / achieve move / untell| W2
  C -->|tell alvos / achieve move / untell| Wn
  C -->|tell alvos / untell / capturado| M
  W1 -->|achieve validar_captura| J
  W2 -->|achieve validar_captura| J
  Wn -->|achieve validar_captura| J
  J -->|captura_confirmada / negada| W1
  J -->|tell captura| C
  W1 -->|tell parede / askAll parede| M
  W2 -->|tell parede / askAll parede| M
  Wn -->|tell parede / askAll parede| M
  W1 & W2 & Wn & J & C -.->|percepts / ações| Ambiente
```

---

## 2. Agentes (especificações Prometheus)

### 2.1 Coordenador

| Campo | Conteúdo |
|---|---|
| **Papel** | Orquestrador da disputa |
| **Objetivos** | Anunciar alvos; dar largada; atualizar placar; remover alvos capturados; encerrar quando não houver alvos livres |
| **Percepções** | Resultado de `listar_alvos()`; mensagem `captura(walker,x,y,valor)` |
| **Ações** | `tell` alvos → Memória e Walkers; `achieve move` → Walkers; `untell alvo` → Memória e rivais; `broadcast encerrar` |
| **Dados** | Lista `capturas`; lista de Walkers |

### 2.2 Memória

| Campo | Conteúdo |
|---|---|
| **Papel** | Blackboard / registro coletivo |
| **Objetivos** | Registrar alvos, capturas e paredes; responder `askAll parede` |
| **Percepções** | Apenas mensagens |
| **Ações** | `tell parede(x,y)` em resposta a `askAll` |
| **Dados** | Crenças `alvo`, `capturado`, `parede` (imutáveis; uma crença por parede) |

### 2.3 Walker (N instâncias — competidores)

| Campo | Conteúdo |
|---|---|
| **Papel** | Agente navegador competitivo |
| **Objetivos** | Capturar o alvo livre de **maior valor**; se empate de valor, o mais próximo (Manhattan) |
| **Percepções** | `agt_position` (própria); `alvo` via `tell`; paredes via colisão e via Memória |
| **Ações** | `move(direção)`; `tell parede` → Memória; `achieve validar_captura` → Juiz; `askAll parede` → Memória |
| **Planos** | `conhecer_alvo`, `mover` (A*), `venci`, `perdi`, `alvo_perdido` (`lose`), `receber_parede`, `encerrar` |

### 2.4 Juiz

| Campo | Conteúdo |
|---|---|
| **Papel** | Arbitragem de captura (exclusão mútua) |
| **Objetivos** | Validar se o Walker está na célula do alvo livre com o valor correto |
| **Percepções** | Estado do percept `alvo` e `agt_position` no ambiente |
| **Ações** | `capturar()`; `tell captura_confirmada` / `captura_negada`; `tell captura` → Coordenador |

---

## 3. Objetivos do sistema (árvore)

```mermaid
mindmap
  root((Sistema PI Walker))
    Orquestrar disputa
      Anunciar 2 alvos
      Dar largada
      Encerrar e rankear
    Competir por valor
      Priorizar alvo de maior valor
      Planejar A* com mapa parcial
      Descobrir paredes por colisão
    Compartilhar conhecimento residual
      Reportar paredes à Memória
      Consultar Memória após perder disputa
    Garantir captura justa
      Validar posição e valor
      Serializar reivindicações
```

---

## 4. Protocolo de interação (cenário principal)

```mermaid
sequenceDiagram
    participant C as Coordenador
    participant M as Memória
    participant W as Walkers
    participant J as Juiz
    C->>M: tell alvo(x,y,valor) ×2
    C->>W: tell alvo(x,y,valor) ×2
    C->>W: achieve move
    loop cada passo
        W->>W: A* até o alvo livre de maior valor
        W-->>M: tell parede(x,y) (quando bate numa parede)
    end
    W->>J: achieve validar_captura(x,y,valor)
    alt chegou primeiro
        J->>W: tell captura_confirmada(valor)
        J->>C: tell captura(walker,x,y,valor)
        C->>M: tell capturado(...) / untell alvo(...)
        C->>W: untell alvo(...) (rivais)
        W->>M: askAll parede(Any,Any)
        M-->>W: tell parede(x,y) (uma por parede)
    else alvo já tomado
        J->>W: tell captura_negada(x,y,motivo)
    end
    C->>W: broadcast tell encerrar (quando não há alvos livres)
```

### Performativas utilizadas

| Performativa | Uso |
|---|---|
| `tell` | Anunciar alvos, paredes, confirmação/negação, placar |
| `untell` | Remover alvo capturado das crenças dos rivais (dispara plano `lose`) |
| `achieve` | Largada (`move`) e validação (`validar_captura`) |
| `askAll` | Perdedor pede todas as paredes conhecidas à Memória |
| `broadcast` | Fim da disputa (`encerrar`) |

---

## 5. Diagrama de agentes × percepções × ações

```mermaid
flowchart TB
  subgraph Walker
    WP[Percepções: agt_position, tell alvo/parede, untell alvo]
    WA[Ações: move, tell parede, achieve validar, askAll]
  end
  subgraph Coordenador
    CP[Percepções: listar_alvos, tell captura]
    CA[Ações: tell/untell alvo, achieve move, broadcast encerrar]
  end
  subgraph Memoria
    MP[Percepções: tell/untell alvo, tell parede, askAll]
    MA[Ações: tell parede em resposta]
  end
  subgraph Juiz
    JP[Percepções: Goal validar_captura + estado Map]
    JA[Ações: capturar, tell confirmada/negada/captura]
  end
```

---

## 6. Cenários Prometheus (resumo)

1. **Inicialização**: Coordenador lê alvos livres, anuncia a Memória e aos Walkers, dispara `move`.
2. **Corrida pelo maior valor**: Todos os Walkers priorizam o alvo de valor 50 (padrão); A* com custo 1,25 em células desconhecidas.
3. **Descoberta de parede**: Colisão → Walker atualiza `Wall_Set` e `tell` à Memória.
4. **Captura válida**: Walker na célula → Juiz confirma → Coordenador atualiza placar e `untell` o alvo.
5. **Captura negada / alvo perdido**: Walker remove o alvo, consulta Memória e replaneja para o próximo alvo livre.
6. **Encerramento**: Sem alvos livres → ranking → `broadcast encerrar` → agentes param o ciclo.

---

## 7. Decisões de desenho (ligação PRO ↔ MOD)

| Decisão | Motivo |
|---|---|
| Sem Q-learning neste PI | Política de um único alvo fica obsoleta quando o alvo some; competição = corrida com A* |
| Mapa compartilhado só via Memória | Walkers são rivais; só quem perde recebe o mapa coletivo |
| Juiz separado | Serializa capturas e evita dois donos para o mesmo alvo |
| Comunicação assíncrona | Evita deadlock de `ask*Reply` no ciclo MASPy |
| Contornos em `Base_Ag.Membro` | Bug de `untell` com lock não reentrante no maspy-ml 2026.5.13 |

---

## 8. Como usar no Draw.io / Miro

1. Copie cada bloco ` ```mermaid ` … ` ``` ` para [mermaid.live](https://mermaid.live) e exporte SVG/PNG.
2. Ou use o plugin Mermaid do Draw.io (`Arrange → Insert → Advanced → Mermaid`).
3. Os quadros das seções 2.x viram cartões de “Agent Descriptor” no Miro.

---

## 9. Rastreabilidade

| Artefato Prometheus | Onde está no código |
|---|---|
| System overview | Este doc + `README.md` de `pi-walker/` |
| Agent descriptors | `Equipe_Ag.py`, `Walker_Ag.py` |
| Interaction protocol | Sequência acima (= README do protótipo) |
| Environment model | `Map_Env.py` |
