# PP — Ambiente de Tarefa PEAS
## Projeto Inicial — Sistemas Multiagentes (PPGCA/UTFPR)
### Tema: Walkers competindo por alvos de valores diferentes (MASPy)

Este documento especifica o ambiente de tarefa do protótipo **PRO** (`pi-walker/`) no formato **PEAS** (Performance, Environment, Actuators, Sensors), e classifica os tipos de agentes do sistema.

---

## 1. Descrição do problema

Em um grid 2D parcialmente observável, com paredes e dois alvos de **valores diferentes** (padrão: 10 e 50), vários agentes **Walker** competem pelo alvo de maior valor. A arquitetura multiagente inclui papéis de coordenação, memória compartilhada e arbitragem de captura, inspirados no padrão Orquestrador/Memória/Dev/QA da Aula 7 e adaptados ao domínio de navegação.

---

## 2. PEAS do ambiente de tarefa

### 2.1 Performance (medida de desempenho)

| Critério | Definição operacional |
|---|---|
| **Valor capturado** | Soma dos valores dos alvos cujo `dono` é o Walker (medida principal da competição). |
| **Ordem de chegada** | Quem chega primeiro ao alvo livre e passa na validação do Juiz leva o ponto; o segundo é negado. |
| **Passos até captura** | Número de movimentos até a captura (métrica secundária de eficiência). |
| **Descoberta de mapa** | Paredes descobertas e reportadas à Memória (métrica colaborativa residual; rivais só recebem esse mapa após perder uma disputa). |

No fim da disputa, o Coordenador imprime o ranking por valor capturado (ex.: `Walker_4=50, Walker_3=10`).

### 2.2 Environment (ambiente)

| Dimensão | Classificação neste problema |
|---|---|
| **Observabilidade** | **Parcialmente observável.** Cada Walker percebe apenas a própria posição (`agt_position`) e descobre paredes ao colidir. Não enxerga a posição dos rivais nem o mapa completo. |
| **Determinismo** | **Determinístico** nas regras de movimento e captura; a geração inicial do mapa (paredes e posições dos alvos) é estocástica. |
| **Episódico vs. sequencial** | **Sequencial.** Cada passo depende do mapa parcial e dos alvos ainda livres. |
| **Estático vs. dinâmico** | **Dinâmico (semi-dinâmico).** O grid físico não muda, mas o estado da disputa muda: alvos livres → capturados; rivais se movem; a Memória acumula paredes. |
| **Discreto vs. contínuo** | **Discreto.** Grid \(W \times H\), ações de movimento cardinal, valores de alvo inteiros. |
| **Agentes** | **Multiagente competitivo** entre Walkers; Coordenador, Memória e Juiz são agentes de suporte (não competem pelo placar). |
| **Conhecido vs. desconhecido** | O modelo de transição (`move`, paredes) é conhecido; a **configuração concreta** (paredes, posições iniciais) é desconhecida a priori para os Walkers. |

**Elementos concretos do ambiente (`Map`):**
- Grid \(W \times H\) (padrão \(10 \times 10\)).
- Paredes com probabilidade configurável (padrão 20%), geradas com garantia de conectividade entre alvos.
- **Dois alvos** com valores distintos (padrão 10 e 50), sorteados com distância mínima.
- Perceptos: `alvo(x,y,valor,dono)`, `wall(x,y)`, `agt_position(x,y)` por Walker.
- Operações: `move(agt, direção)`, `listar_alvos()`, `capturar(walker, x, y, valor)`.

### 2.3 Actuators (atuadores)

| Agente | Atuadores / efeitos |
|---|---|
| **Walker** | `move(direção)` no ambiente (`up`/`down`/`left`/`right`/`stay`); envio de mensagens (`tell` parede, `achieve` validar_captura, `askAll` paredes). |
| **Coordenador** | Anúncio de alvos (`tell`), largada (`achieve move`), remoção de alvos (`untell`), broadcast `encerrar`. |
| **Memória** | Respostas a `askAll` com `tell parede(x,y)`; registro interno de alvos/capturas. |
| **Juiz** | Chamada a `capturar()` no ambiente; `tell captura_confirmada` / `captura_negada`; notificação ao Coordenador. |

### 2.4 Sensors (sensores)

| Agente | Sensores / percepções |
|---|---|
| **Walker** | Percepto filtrado `agt_position` (própria posição); crenças de alvos e paredes via mensagens; feedback de colisão (posição não muda após `move`). |
| **Coordenador** | `listar_alvos()` no ambiente; mensagens `captura(...)` do Juiz. |
| **Memória** | Apenas mensagens (`tell`/`untell`/`askAll`). |
| **Juiz** | Estado dos alvos e posições via ambiente no momento de `capturar()`. |

---

## 3. Tipos de agentes

| Agente | Tipo (Russell & Norvig / SMA) | Justificativa breve |
|---|---|---|
| **Walker** | Agente baseado em objetivos (goal-based), com planejamento local (A*) sobre mapa parcial; competitivo. | Escolhe o alvo livre de maior valor (empate: mais perto), planeja caminho e reage a `untell`/negação replanejando. |
| **Coordenador** | Agente reativo baseado em objetivos de orquestração. | Dispara a disputa, mantém o placar e encerra quando não há alvos livres. |
| **Memória** | Agente de serviço / blackboard leve. | Acumula conhecimento coletivo (alvos, capturas, paredes) e responde consultas. |
| **Juiz** | Agente reativo de arbitragem. | Serializa reivindicações de captura e garante exclusão mútua do alvo. |

### Critério de decisão do Walker (competição)

\[
\text{objetivo}(pos) = \arg\max_{a \in AlvosLivres} \bigl( valor(a),\; -manhattan(pos, a) \bigr)
\]

Assim, **todos competem primeiro pelo alvo de maior valor**; só após esse alvo sair da disputa (via `untell`) os restantes passam a buscar o de menor valor.

---

## 4. Propriedades do sistema multiagente

- **Comunicação**: canal MASPy assíncrono (`tell`, `untell`, `achieve`, `askAll`, `broadcast`). Não se usa `askOneReply`/`askAllReply` para evitar bloqueio.
- **Organização**: papéis especializados (coordenação, memória, competidores, juízo).
- **Concorrência**: vários Walkers em ciclos paralelos; o Juiz serializa capturas no ambiente.
- **Incerteza**: mapa parcial + descoberta por colisão (custo 1,25 em células desconhecidas no A*).

---

## 5. Mapeamento para o protótipo

| Elemento PEAS | Arquivo / símbolo |
|---|---|
| Ambiente | `Map_Env.py` (`Map`) |
| Walker | `Walker_Ag.py` |
| Coordenador / Memória / Juiz | `Equipe_Ag.py` |
| Entrada do sistema | `Walker_Main.py` (`--sem-gui` ou menu Pygame) |

---

## 6. Referências de apoio

- Russell, S.; Norvig, P. *Artificial Intelligence: A Modern Approach* — ambiente de tarefa PEAS.
- Wooldridge, M. *An Introduction to MultiAgent Systems* — agentes, comunicação, coordenação.
- Exemplo base MASPy: `2D-Navigation-Learn` (LaCA-IS/MASPY).
