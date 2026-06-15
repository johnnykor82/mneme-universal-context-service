# Prompt for Next Session: Mneme Universal Context Service Phase 14

Это не текст "на почитать". Это инструкция к выполнению. Начни работу сразу после
прочтения и продолжай автономно по плану, пока не появится реальный блокер,
новая инструкция пользователя или архитектурная неопределенность, которую нельзя
разрешить из файлов проекта.

## Scope

Проект:

`/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`

Работать только в этом каталоге.

Нельзя модифицировать:

- `/Users/openclaw/.hermes/hermes-agent`
- `/Users/openclaw/.hermes/plugins/hermes-mneme`

Можно читать read-only reference paths, если нужно для понимания parity:

- `/Users/openclaw/.hermes/plugins/_hermes-mneme-native`
- `/Users/openclaw/.hermes/plugins/_hermes-agent-pr`

Но не менять их.

## Required Skills and Workflow

Обязательно используй:

- `planning-with-files`
- `test-driven-development`

Перед работой прочитай:

- `task_plan.md`
- `progress.md`
- `findings.md`
- `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
- `HERMES_MNEME_COMPARISON.md`
- `API_MCP_CONTRACT_V0.md`
- `MNEME_HOST_ADAPTER_CONTRACT_V0.md`

Также запусти planning catchup:

```bash
python3 /Users/openclaw/CodexShared/skills/planning-with-files/scripts/session-catchup.py /Users/openclaw/.hermes/plugins/_mneme-universal-context-service
```

Если catchup показывает несинхронизированный контекст, сначала разберись и
обнови planning files.

## Autonomy Rule

Не останавливайся после одного маленького task и не жди, что пользователь
напишет "продолжай".

Продолжай выполнять следующие Phase 14 tasks по порядку, используя TDD и
обновляя planning files, пока выполняется хотя бы одно условие:

- следующий task понятен из `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`;
- есть локальные тесты, которыми можно зафиксировать поведение;
- решение можно вывести из существующего кода, контрактов и reference
  implementation без архитектурной догадки.

Останавливайся и спрашивай пользователя только если:

- нужно выбрать продуктовую/архитектурную политику, которой нет в планах;
- есть несколько несовместимых вариантов и выбор повлияет на публичный контракт;
- нужно трогать live Hermes или live `hermes-mneme`;
- нужно делать network/provider calls, устанавливать зависимости или менять
  внешнюю конфигурацию за пределами project root;
- тесты показывают конфликт требований, который нельзя честно разрешить.

Не придумывай недостающие требования ради продвижения. Если данных не хватает,
сформулируй конкретный вопрос пользователю и укажи, какие варианты ты видишь.

## Current Status

Phase 14: Hermes-Mneme functional parity recovery is in progress.

Completed:

- Phase 14 Task 1: Provider Config Foundation.
- `ProviderSettings`, `load_settings()`, `mneme.example.toml`,
  provider-aware `/v1/capabilities`, and `mneme serve` provider/config flags.
- Last verification:
  - focused config tests: `4 passed, 1 warning`
  - full pytest: `30 passed, 1 warning`
  - `py_compile`: passed
  - `mneme serve --help`: passed

Next action:

Start Phase 14 Task 2: Embedding Provider and Index.

## Execution Plan

Work through as many of these as possible in one session:

1. Phase 14 Task 2: Embedding Provider and Index.
   - Write RED tests first in `tests/test_embeddings.py`.
   - Implement provider abstraction, OpenAI/Jina-compatible HTTP client shape,
     SQLite embedding index tables, Python cosine fallback, batch embedding path,
     provider circuit breaker, and "store event even when embedding fails".
   - Do not make hidden real provider calls in tests. Use mock/in-process HTTP
     transports or fake providers.

2. Phase 14 Task 3: Hybrid Retrieval Pipeline.
   - Start only after Task 2 is green.
   - Write RED tests first in `tests/test_retrieval.py`.
   - Integrate semantic retrieval with keyword/recency fallback.
   - Preserve REST/MCP parity and memory-read audit behavior.

3. Phase 14 Task 4: Execution State and Goal History.
   - Start only after Task 3 is green.
   - Write RED tests first in `tests/test_state.py`.
   - Add versioned execution state/state history behavior without tying it to
     Hermes internals.

If a task is too large, complete the smallest coherent TDD slice, verify it,
update planning files, then continue to the next coherent slice.

## Verification Requirements

After each implementation slice:

```bash
.venv/bin/python -m pytest <focused test file or test node> -q
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile mneme_service/*.py
```

Also run relevant smoke/scans when files are changed:

```bash
rg -n "^(<<<<<<<|=======|>>>>>>>)" <changed files>
rg -n "[[:blank:]]$" <changed files>
```

Record all RED/GREEN/full verification results in `progress.md`.

## Planning Updates

After each completed task or important discovery:

- update `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`;
- update `task_plan.md`;
- update `findings.md` if a decision/discovery was made;
- update `progress.md` with actions, files, tests, and next action.

The 5-question reboot check in `progress.md` must remain accurate.

## Important Direction

The project is intentionally paused on Codex dogfood polish, GitHub publication,
Hermes adapter, and other adapters until Phase 14 parity recovery provides real
semantic/execution-state memory.

Runtime-neutral session/topic drift semantics belong in the daemon. Host-specific
hook plumbing belongs in adapters.

Do not implement provider network calls beyond local mocked/fake test paths in
this milestone slice unless the plan explicitly reaches that step and tests make
it safe.
