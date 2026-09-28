# refactor-arch — Skill de Refatoração Arquitetural Automatizada

Uma **Skill do Claude Code** que analisa, audita e refatora qualquer codebase de
backend para o padrão **MVC**, de forma **agnóstica de tecnologia**. A mesma
skill roda nos três projetos deste repositório (Python/Flask e Node.js/Express),
detectando a stack, gerando um relatório de auditoria e reestruturando o código —
sempre pedindo confirmação humana antes de tocar em qualquer arquivo.

A skill vive em `<projeto>/.claude/skills/refactor-arch/` e é invocada com
`claude "/refactor-arch"`.

> Estrutura da skill:
> ```
> .claude/skills/refactor-arch/
> ├── SKILL.md                              # workflow das 3 fases (o "prompt")
> └── references/                           # conhecimento de domínio
>     ├── 01-project-analysis.md            # heurísticas de detecção de stack
>     ├── 02-antipattern-catalog.md         # catálogo de anti-patterns + severidade
>     ├── 03-audit-report-template.md       # formato do relatório (Fase 2)
>     ├── 04-mvc-architecture-guidelines.md # regras do MVC alvo
>     └── 05-refactoring-playbook.md        # transformações antes/depois (Fase 3)
> ```

---

## A) Análise Manual

Antes de construir a skill, cada projeto foi lido linha a linha. Abaixo os
achados que guiaram o catálogo de anti-patterns. (Os relatórios completos gerados
pela skill estão em [`reports/`](reports/).)

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)
Monólito de 4 arquivos (~780 linhas), sem separação de camadas.

| # | Severidade | Problema | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | SQL Injection por concatenação de strings em todas as queries | `models.py:28,48,110,…` | Qualquer cliente lê/apaga o banco e faz bypass de login (`' OR '1'='1`) |
| 2 | **CRITICAL** | Endpoint `/admin/query` executa SQL arbitrário do body | `app.py:59-78` | Equivalente a RCE sobre o banco, sem autenticação |
| 3 | **CRITICAL** | `/admin/reset-db` apaga todas as tabelas sem proteção | `app.py:47-57` | Perda total de dados por qualquer anônimo |
| 4 | **CRITICAL** | Senhas em texto puro (armazenadas, comparadas e retornadas em `GET /usuarios`) | `models.py:83,110,127` | Comprometimento total de credenciais |
| 5 | **CRITICAL** | `SECRET_KEY` hardcoded e vazada no `/health` | `app.py:7`, `controllers.py:289` | Forja de sessão; segredo não rotacionável |
| 6 | **CRITICAL** | God Module: 4 domínios + SQL + lógica + validação num arquivo | `models.py:1-314` | Impossível testar isolado; SRP violado |
| 7 | **HIGH** | Conexão global mutável compartilhada entre threads | `database.py:4-10` | Race conditions; acoplamento oculto |
| 8 | **HIGH** | Lógica de negócio e notificações dentro dos controllers | `controllers.py:208-210`, `models.py:235-273` | Fat controller; regra no lugar errado |
| 9 | **HIGH** | `DEBUG=True` em "produção" | `app.py:8` | Debugger interativo exploitável |
| 10 | **MEDIUM** | N+1 ao listar pedidos (query por item e por produto) | `models.py:187-199,219-231` | Escala mal |
| 11 | **MEDIUM** | Validação duplicada/ausente (tipos não checados) | `controllers.py:30-54` | Dados inválidos no banco |
| 12 | **MEDIUM** | Criação de schema misturada com seed no `get_db` | `database.py:12-84` | Efeitos colaterais escondidos |
| 13 | **LOW** | Magic numbers nas faixas de desconto | `models.py:257-262` | Ilegível |
| 14 | **LOW** | `print()` como log | `controllers.py:*` | Sem controle de logging |
| 15 | **LOW** | Dicts de serialização duplicados | `models.py` | Duplicação |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)
God class `AppManager` + globals mutáveis em `utils.js` (~180 linhas).

| # | Severidade | Problema | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | Credenciais/segredos hardcoded (`dbPass`, `paymentGatewayKey`) | `utils.js:1-7` | Chave de pagamento *live* no código |
| 2 | **CRITICAL** | Número do cartão e chave do gateway logados no console | `AppManager.js:45` | Violação de PCI; segredos nos logs |
| 3 | **CRITICAL** | "Criptografia" caseira (`badCrypto`) para senhas | `utils.js:17-23` | Hash reversível/inútil |
| 4 | **CRITICAL** | God Class `AppManager` (DB + rotas + lógica) | `AppManager.js:1-141` | Intestável; SRP violado |
| 5 | **HIGH** | Callback hell (checkout com 5 níveis de aninhamento) | `AppManager.js:37-77` | Frágil, ilegível |
| 6 | **HIGH** | Sem transação no checkout; `DELETE user` deixa órfãos | `AppManager.js:50-63,131-137` | Dados corrompidos/parciais |
| 7 | **HIGH** | Estado global mutável (`globalCache`, `totalRevenue`) | `utils.js:9-10` | Acoplamento oculto |
| 8 | **MEDIUM** | N+1 no relatório financeiro com contadores manuais | `AppManager.js:83-127` | O(cursos·matrículas·2) |
| 9 | **MEDIUM** | Validação fraca; "pagamento" = `card.startsWith("4")` | `AppManager.js:28-35,47` | Lógica ingênua |
| 10 | **MEDIUM** | Respostas inconsistentes (`send` texto vs `json`) | `AppManager.js:*` | Contrato imprevisível |
| 11 | **LOW** | Nomes crípticos (`u,e,p,cid,cc`) | `AppManager.js:29-33` | Ilegível |
| 12 | **LOW** | Código morto (`totalRevenue` importado e nunca usado) | `utils.js:10` | Ruído |
| 13 | **LOW / DEP** | Driver `sqlite3` callback-based (API legada) | `AppManager.js:*` | Recomendado wrapper/promises |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager)
Parcialmente organizado (`models/`, `routes/`, `services/`, `utils/`), mas com
lógica presa nas rotas e `services/` nunca usado (~1150 linhas).

| # | Severidade | Problema | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | Credenciais SMTP e `SECRET_KEY` hardcoded | `services/notification_service.py:7-10`, `app.py:13` | Segredos no VCS |
| 2 | **CRITICAL** | Hash de senha MD5 sem sal | `models/user.py:29,32` | Quebrável por rainbow table |
| 3 | **HIGH** | `to_dict()` expõe o hash da senha em todas as respostas | `models/user.py:19-24` | Vazamento de hashes |
| 4 | **HIGH** | Lógica de negócio nas rotas; sem camada de controller; `services/` morto | `routes/*.py` | Fat controller; abstrações mortas |
| 5 | **HIGH** | N+1 em listagens e relatórios | `task_routes.py:42-57`, `report_routes.py:53-68` | Escala mal |
| 6 | **HIGH** | Regra de "overdue" duplicada em ~4 handlers (e `is_overdue()` não usada) | `task_routes.py:30-39`, `report_routes.py:34-43` | Lógica dessincroniza |
| 7 | **MEDIUM / DEP** | `datetime.utcnow()` deprecado (Python 3.12+) | vários | Warnings/remoção futura |
| 8 | **MEDIUM / DEP** | `Model.query.get()` legado (SQLAlchemy 2.0) | vários | Warnings/remoção futura |
| 9 | **MEDIUM** | `except:` nu engolindo erros | `task_routes.py:62,…` | Bugs invisíveis |
| 10 | **MEDIUM** | Validação triplicada (rota + helper + model), só a da rota usada | `helpers.py:57-108` | Regras inconsistentes |
| 11 | **LOW** | Imports mortos (`os, sys, json, math, hashlib`) | vários | Ruído |
| 12 | **LOW** | Token JWT falso | `user_routes.py:210` | Enganoso |
| 13 | **LOW** | `/categories` dentro do blueprint de reports | `report_routes.py:157-223` | Roteamento confuso |
| 14 | **LOW** | Contagem de prioridade repetitiva (5 counts) | `report_routes.py:24-28` | Duplicação |

---

## B) Construção da Skill

### Decisões de design
- **`SKILL.md` é o "prompt", as referências são o "conhecimento".** O `SKILL.md`
  descreve só o *workflow* das 3 fases e as regras de ouro (nunca editar antes da
  confirmação; preservar comportamento; citar `arquivo:linha`; adaptar ao ponto
  de partida). O conhecimento de domínio foi isolado em 5 arquivos de referência
  carregados sob demanda no início de cada fase — mantendo o `SKILL.md` enxuto e
  fácil de manter.
- **5 áreas de conhecimento, 5 arquivos** (mapeamento 1:1 com o exigido): análise
  de projeto, catálogo de anti-patterns, template de relatório, guidelines de
  MVC e playbook de refatoração.
- **Gate de confirmação explícito** ao fim da Fase 2 (`[y/n]`) — obrigatório
  antes de qualquer escrita.
- **Validação obrigatória** na Fase 3: subir a aplicação + exercitar os endpoints
  originais; regressões são corrigidas antes de declarar sucesso.
- **Ledger de resolução com evidência** na Fase 3: cada *parte* da recomendação
  de cada finding é conferida no código já refatorado (grep de call sites,
  grep do token deprecated no projeto inteiro, resposta do endpoint). Um
  finding só conta como resolvido quando todas as partes passam — nada de
  "N/N resolvidos" sem prova.

### Anti-patterns incluídos (e por quê)
O catálogo tem **20+ anti-patterns** cobrindo as 4 severidades, agrupados em:
segurança (`AP-SEC-*`: segredos hardcoded, SQL injection, hashing fraco,
vazamento de dados, endpoints perigosos, debug em prod), arquitetura/SOLID
(`AP-ARCH-*`: God class, lógica no controller, estado global, sem service layer,
sem transação), performance/correção (`AP-PERF-*`, `AP-VAL-*`, `AP-ERR-*`: N+1,
callback hell, validação, erros engolidos), **APIs deprecated** (`AP-DEP`, com
tabela API antiga → substituto moderno) e qualidade (`AP-LOW-*`: magic numbers,
código morto, nomes, duplicação). Foram escolhidos exatamente por serem os
padrões observados na análise manual dos 3 projetos — de monólito totalmente
desestruturado a projeto parcialmente organizado.

### Como garanti que a skill é agnóstica de tecnologia
- A **Fase 1 detecta** linguagem/framework/DB por manifesto + confirmação no
  código, em vez de assumir.
- O catálogo e as guidelines descrevem **responsabilidades universais**, não
  sintaxe: "a camada de rotas só faz HTTP", "models são o único lugar que fala
  com o banco". Os *nomes* das camadas podem variar (`views` vs `routes`,
  `controllers` vs `services`) mas o papel é o mesmo.
- O playbook traz exemplos **em Python e em JS** lado a lado.
- A skill **classifica o ponto de partida** (monólito / parcialmente em camadas /
  limpo) e adapta o esforço — foi isso que permitiu tratar o monólito do Projeto
  1 e o já-organizado Projeto 3 de formas diferentes com a mesma skill.

### Desafios encontrados e como resolvi
- **`datetime.utcnow()` deprecado vs. datas naive no SQLite.** Trocar por
  `datetime.now(timezone.utc)` (aware) quebraria as comparações com as datas
  *naive* já gravadas. Resolvi com um único helper `utc_now()` que devolve UTC
  *naive*, eliminando a API deprecada sem quebrar comparações.
- **Preservar o contrato dos endpoints** enquanto se troca o hashing de senha:
  mantive as assinaturas `set_password`/`check_password` e re-seedei os usuários
  já com hash, então o login continua funcionando.
- **Endpoints perigosos** (`/admin/query`, `/admin/reset-db`): são CRITICAL,
  mas removê-los quebraria o contrato ("endpoints originais respondem"). A
  solução foi manter as rotas de forma segura: `/admin/query` responde **410
  Gone** e nunca executa SQL; `/admin/reset-db` responde **403** a menos que
  `ADMIN_TOKEN` esteja configurado e seja enviado em `X-Admin-Token`, e então
  executa só DELETEs fixos numa transação.
- **Feedback da revisão (Projeto 3): "wired" sem nenhuma chamada.** O relatório
  da 1ª execução dizia que o `NotificationService` estava conectado e fechava
  em 14/14, mas ele e o `process_task_data` continuavam sem nenhuma chamada. A
  causa foi a Fase 3 resumir o que *pretendia* fazer, e não o que o código
  mostrava. Correção na skill: (1) regra de ouro nº 6 ("resolvido precisa ser
  provado"); (2) passo 5 da Fase 3 com o checklist de verificação por tipo de
  recomendação (wire → call site alcançável; remove → grep vazio; deprecated →
  grep no projeto inteiro, incluindo seeds/helpers); (3) ledger obrigatório no
  relatório; (4) catálogo `AP-ARCH-05` e playbook `PB-07` com exemplo concreto
  de "wiring". A skill foi executada de novo no Projeto 3 (Run 2 em
  `reports/audit-project-3.md`): achou 10 pendências (entre elas as duas
  apontadas, `utcnow()` no `seed.py`, `except:` nu nos helpers e uma mensagem
  de erro do `PUT /tasks` que tinha mudado) e fechou todas com evidência.
- **Projeto 3 já organizado:** em vez de forçar tudo para dentro de `src/`,
  mantive `models/routes/services/utils` e *adicionei* as camadas que faltavam
  (`config/`, `controllers/`, `middlewares/`) — demonstrando adaptação ao
  contexto.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 1 · code-smells-project | Python/Flask | 6 | 3 | 3 | 3 | **15** |
| 2 · ecommerce-api-legacy | Node.js/Express | 4 | 3 | 3 | 3 | **13** |
| 3 · task-manager-api (Run 1) | Python/Flask | 2 | 4 | 4 | 4 | **14** |
| 3 · task-manager-api (Run 2, re-auditoria) | Python/Flask | 0 | 2 | 4 | 4 | **10** |

No Projeto 3, o Run 2 audita o código depois do Run 1 e lista o que ficou
pendente. O ledger final fecha os 24 findings com evidência.

Detecção de **APIs deprecated**: Projeto 2 (driver sqlite3 callback-based) e
Projeto 3 (`datetime.utcnow()`, `Query.get()`, MD5) — todas substituídas.

### Antes / Depois da estrutura

**Projeto 1 (monólito → MVC completo):**
```
Antes:  app.py, controllers.py, models.py, database.py   (tudo misturado)
Depois: src/{config,models,controllers,views,middlewares,services}/ + app.py (factory)
```
**Projeto 2 (God class → MVC + DI):**
```
Antes:  src/{app.js, AppManager.js, utils.js}            (AppManager faz tudo)
Depois: src/{config,database,models,controllers,routes,services,middlewares}/ + app.js
```
**Projeto 3 (parcialmente organizado → camadas completadas):**
```
Antes:  models/ routes/ services/(morto) utils/ app.py   (lógica nas rotas)
Depois: + config/ + controllers/ + middlewares/ + utils/dates.py + errors.py
        (rotas finas; NotificationService chamado pelo task_controller;
         process_task_data como único validador; categorias em blueprint próprio)
```

### Checklist de Validação (preenchido para os 3 projetos)

| Item | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| **Fase 1** — Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| **Fase 1** — Framework detectado corretamente | ✅ | ✅ | ✅ |
| **Fase 1** — Domínio descrito corretamente | ✅ | ✅ | ✅ |
| **Fase 1** — Nº de arquivos condiz com a realidade | ✅ | ✅ | ✅ |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| **Fase 2** — Cada finding tem arquivo e linhas | ✅ | ✅ | ✅ |
| **Fase 2** — Findings ordenados por severidade | ✅ | ✅ | ✅ |
| **Fase 2** — Mínimo de 5 findings | ✅ (15) | ✅ (13) | ✅ (14) |
| **Fase 2** — Detecção de APIs deprecated | n/a¹ | ✅ | ✅ |
| **Fase 2** — Pausa e pede confirmação | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura de diretórios MVC | ✅ | ✅ | ✅ |
| **Fase 3** — Config extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| **Fase 3** — Models abstraem os dados | ✅ | ✅ | ✅ |
| **Fase 3** — Views/Routes separadas | ✅ | ✅ | ✅ |
| **Fase 3** — Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| **Fase 3** — Error handling centralizado | ✅ | ✅ | ✅ |
| **Fase 3** — Entry point claro | ✅ | ✅ | ✅ |
| **Fase 3** — Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| **Fase 3** — Endpoints originais respondem | ✅ | ✅ | ✅ |

¹ Projeto 1 não usa APIs deprecated; o relatório registra "No deprecated APIs
detected" (o problema é *como* o SQL é montado, coberto por AP-SEC-02).

### Logs das aplicações rodando após a refatoração

**Projeto 1 — `python -m src.app` + 21 checks de endpoints:**
```
==================================================
SERVIDOR INICIADO — http://localhost:5000
==================================================
 * Debug mode: off
GET /health -> {"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok"}
21/21 checks passed  (produtos, usuarios, login, pedidos, relatorios, health)
  ✓ no password leak in /usuarios     ✓ no secret_key in /health
  ✓ POST /admin/query -> 410 (SQL nunca executado)
  ✓ POST /admin/reset-db -> 403 sem token / 200 com X-Admin-Token válido
```
**Projeto 2 — `node src/app.js` + 7 checks:**
```
7/7 checks passed
  ✓ POST /api/checkout (success/denied/bad-request)
  ✓ GET /api/admin/financial-report (JOIN, revenue presente)
  ✓ DELETE /api/users/:id (cascade, sem órfãos)
```
**Projeto 3 — `flask --app app run` + 39 checks (Run 2, com DeprecationWarning → erro):**
```
 * Debug mode: off
GET /health -> {"status":"ok", ...}
39/39 checks passed  (tasks CRUD/search/stats, users CRUD, login, reports, categories CRUD)
  ✓ create with user_id notifies (NotificationService wired)
  ✓ reassign notifies / update sem reatribuição não notifica
  ✓ mensagens de validação originais (POST e PUT /tasks)
  ✓ POST non-int priority -> 400 (antes 500)
pyflakes: limpo
```

### Observações sobre stacks diferentes
- Em **Python** o padrão natural foi módulos-função por camada (blueprints Flask,
  funções de model); em **Node** foi classes com **injeção de dependência** no
  composition root — a skill mapeou as mesmas responsabilidades nos dois idiomas.
- A skill se comportou diferente por **ponto de partida**: split total no
  monólito (P1/P2) vs. *completar camadas* preservando o que já era bom (P3),
  exatamente como as guidelines instruem.
- O gate de confirmação e a validação por endpoints funcionaram igual nas 3
  stacks, provando que o *workflow* é agnóstico e só o *conhecimento* das
  referências é aplicado ao contexto.

---

## D) Como Executar

### Pré-requisitos
- **Claude Code** instalado e configurado.
- **Python 3.11+** (Projetos 1 e 3) e **Node.js 18+** (Projeto 2).

### Rodar a skill em cada projeto
```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```
A skill imprime o resumo da Fase 1, o relatório da Fase 2 e **pausa** pedindo
`[y/n]`. Responda `y` para executar a refatoração (Fase 3).

### Validar que a refatoração funciona (código já refatorado neste repo)
```bash
# Projeto 1 (Python/Flask)
cd code-smells-project
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
PYTHONPATH=. ./.venv/bin/python -m src.app        # sobe em :5000
curl localhost:5000/health

# Projeto 2 (Node/Express)
cd ../ecommerce-api-legacy
npm install && npm start                          # sobe em :3000
# requisições de exemplo em api.http

# Projeto 3 (Python/Flask)
cd ../task-manager-api
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
PYTHONPATH=. ./.venv/bin/python seed.py           # popula o banco
PYTHONPATH=. ./.venv/bin/python -m flask --app app run   # sobe em :5000
curl localhost:5000/tasks
```

### Ordem de execução sugerida
1. **Análise manual** dos 3 projetos (feita na seção A).
2. **Criar a skill** (`SKILL.md` + referências) — em `code-smells-project`.
3. **Executar** nos 3 projetos, salvando a saída da Fase 2 em
   `reports/audit-project-{1,2,3}.md`.
4. **Iterar** ajustando as referências conforme necessário.

### Onde está cada entregável
- Skill: `code-smells-project/.claude/skills/refactor-arch/` (e cópias em
  `ecommerce-api-legacy/` e `task-manager-api/`).
- Código refatorado: `src/` (P1, P2) e camadas adicionadas (P3).
- Relatórios: [`reports/audit-project-1.md`](reports/audit-project-1.md),
  [`2`](reports/audit-project-2.md), [`3`](reports/audit-project-3.md).
