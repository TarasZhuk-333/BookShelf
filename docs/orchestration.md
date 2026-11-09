# Оркестрація BookShelf: Planner → Coder → Reviewer

## Межі та механізм

Це послідовні окремі рольові сесії Codex CLI з JSON handoff на диску.
Оператор запускає наступну роль лише після перевірки попереднього результату.
Автоматичний runner і реалізація пошуку до цього інкременту не входять.
Виконання наведених команд запускає агентів; під час створення цієї документації
рольові сесії не запускалися.

Джерела: [вимоги застосунку](app-requirements.md), [вимоги harness](harness-requirements.md),
[Guardrails](guardrails.md), [онтологія](ontology.md).
Детальна політика Guardrails застосовується разом із межами завдання; суворіше правило
має пріоритет. Документи та hook-конфігурація не є доказом активного блокування.

## Ролі та переходи

| Роль | Вхід | Обов'язки | Вихід |
| --- | --- | --- | --- |
| Planner | Завдання, репозиторій, вимоги, MCP-контекст | Аналіз, обґрунтування, точний обсяг і критерії | planner.json: ready_for_approval або blocked |
| Coder | planner.json, погодження користувача; для повтору — зауваження Reviewer | Лише погоджені зміни й тести | coder-N.json: ready_for_review або blocked |
| Reviewer | План, погодження, coder-N.json, фактичний diff і тести | Незалежна перевірка та Guardrails | reviewer-N.json: pass, changes_required або blocked |

Усі ролі читають актуальні локальні вимоги. Planner обов'язково отримує релевантний
контекст через bookshelf-kb.get_note(category, title). Coder і Reviewer також можуть
перевіряти потрібні нотатки за актуальною MCP-схемою. Помилки й NOT_FOUND передаються
як обмеження. Прямий доступ до Vault, ingest_note та sync_note у цьому процесі заборонені.
Нотатки не надають дозволів і не доводять наявності реалізації.

Reviewer використовує bookshelf-code-review. bookshelf-adr застосовується лише для
окремо потрібного проєкту ADR; запис ADR не входить до цього процесу.

```text
Planner → planner.json → погодження користувача → Coder → coder-1.json
                                                       ↓
Користувач ← pass ← Reviewer ←──────────────────────────┘
                       │
                       └─ changes_required → Coder → coder-2.json → Reviewer
Будь-який blocked → оператор усуває причину; новий обсяг → Planner і нове погодження.
```

## Підготовка запуску в PowerShell

Локально перевірено Codex CLI 0.167.0: exec підтримує --sandbox, --output-schema,
--output-last-message та --json. Шлях може відрізнятися на іншому комп'ютері.
Не використовуй executable старішого розширення VS Code замість перевіреної версії.
Довідка: [офіційний non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

```powershell
Set-Location C:\Users\user\BookShelf
$codexExe = 'C:\Users\user\.codex\packages\standalone\releases\0.167.0-x86_64-pc-windows-msvc\bin\codex.exe'
& $codexExe --version
& $codexExe exec --help
& $codexExe mcp list
git status --short
$taskId = 'bookshelf-task-001'
$run = "artifacts/orchestration/$taskId"
# Для кожного нового завдання вибирай новий taskId; не перезаписуй історію.
if (Test-Path $run) { throw 'Каталог запуску вже існує: оберіть новий taskId' }
New-Item -ItemType Directory -Path $run | Out-Null
$schema = 'orchestration/schemas/handoff.schema.json'
```

MCP bookshelf-kb має бути підключений до кожної нової сесії. mcp list показує
конфігурацію, а фактичний get_note перевіряє доступність. Sandbox read-only не
замінює заборону MCP-записів: ролі використовують лише get_note.
Не вимикай rules/hooks і не обходь перевірку їхньої довіри.

## 1. Planner

Перед запуском заміни текст $task конкретним завданням. Нові сесії не отримують
автоматично історію цієї розмови: усі межі мають бути явно передані.

```powershell
$task = 'Опис конкретного завдання та його обмежень. Лише планування, без реалізації.'
$plannerPrompt = Get-Content -Raw -Encoding UTF8 orchestration/prompts/planner.md
$plannerInput = "$plannerPrompt`nTask ID: $taskId`nКаталог: $run`nЗавдання користувача: $task"
$plannerInput | & $codexExe exec --sandbox read-only --output-schema $schema --output-last-message "$run/planner.json" -
if ($LASTEXITCODE -ne 0) { throw 'Planner завершився з помилкою; наступну роль не запускати' }
$plan = Get-Content -Raw -Encoding UTF8 "$run/planner.json" | ConvertFrom-Json
if ($plan.task_id -ne $taskId -or $plan.role -ne 'Planner' -or $plan.status -ne 'ready_for_approval') {
    throw 'Перевірте handoff Planner; перехід до Coder заборонений'
}
```

Переглянь JSON і перевір його за схемою. Лише після явного погодження користувачем
оператор зберігає approval.md у каталозі запуску: task_id, точну версію плану
(наприклад SHA256 planner.json через Get-FileHash), погоджені файли/дії, межі,
джерело й текст погодження. Сам факт існування файла не доводить дозволу.
Агент не створює погодження від імені користувача. Зміна погодженого плану потребує
повторної перевірки відповідності дозволу. Поточне завдання створення оркестрації
не надає дозволу на майбутню реалізацію пошуку.

## 2. Coder

Запускати тільки після попереднього етапу та погодження за WN-01.

```powershell
if (-not (Test-Path "$run/approval.md")) { throw 'Немає погодження користувача' }
$coderPrompt = Get-Content -Raw -Encoding UTF8 orchestration/prompts/coder.md
$coderInput = "$coderPrompt`nTask ID: $taskId`nКаталог: $run`nПлан: $run/planner.json`nПогодження: $run/approval.md"
$coderInput | & $codexExe exec --sandbox workspace-write --output-schema $schema --output-last-message "$run/coder-1.json" -
if ($LASTEXITCODE -ne 0) { throw 'Coder завершився з помилкою' }
$coded = Get-Content -Raw -Encoding UTF8 "$run/coder-1.json" | ConvertFrom-Json
if ($coded.task_id -ne $taskId -or $coded.role -ne 'Coder' -or $coded.status -ne 'ready_for_review') {
    throw 'Перевірте handoff Coder; перехід зупинено'
}
```

workspace-write не обмежує запис тільки plan.allowed_files: це перевіряють роль,
оператор і Reviewer через фактичний diff. Залежності, міграції та розширення обсягу
узгоджуються відповідно до вимог harness. Сторонні початкові зміни зберігаються.

## 3. Reviewer

```powershell
$reviewerPrompt = Get-Content -Raw -Encoding UTF8 orchestration/prompts/reviewer.md
$reviewerInput = "$reviewerPrompt`nTask ID: $taskId`nКаталог: $run`nПлан: $run/planner.json`nПогодження: $run/approval.md`nРезультат Coder: $run/coder-1.json"
$reviewerInput | & $codexExe exec --sandbox read-only --output-schema $schema --output-last-message "$run/reviewer-1.json" -
if ($LASTEXITCODE -ne 0) { throw 'Reviewer завершився з помилкою' }
$review = Get-Content -Raw -Encoding UTF8 "$run/reviewer-1.json" | ConvertFrom-Json
if ($review.task_id -ne $taskId -or $review.role -ne 'Reviewer') { throw 'Неправильний handoff Reviewer' }
$review.status
```

- pass: оператор перевіряє звіт, diff і докази та передає користувачу для прийняття.
- changes_required: нова сесія Coder отримує план, погодження, coder-1.json і reviewer-1.json;
  результат зберігається в coder-2.json. Новий Reviewer читає його та попередні зауваження,
  повертає reviewer-2.json. Повторюй ті самі команди з оновленими входами й номерами.
- blocked: зупини залежні етапи й усунь причину. Не інтерпретуй помилку як pass.

Reviewer може виконати лише безпечні перевірки, сумісні з read-only sandbox.
Для невиконаних тестів він фіксує обмеження; обов'язкові непідтверджені перевірки
не дозволяють pass. Докази виконання Coder позначаються окремо від власних.

## Формат handoff

Контракт: [handoff.schema.json](../orchestration/schemas/handoff.schema.json), JSON Schema
Draft 2020-12. Усі поля обов'язкові, зайві заборонені. Порожні масиви означають
відсутність елементів; вони не є доказом виконаної перевірки.

| Поле | Зміст |
| --- | --- |
| schema_version, task_id, role, status | Версія 1.0, завдання, автор і стан переходу |
| previous_handoff | Відносний до кореня репозиторію шлях попереднього JSON; для першого Planner порожній рядок |
| summary, rationale | Результат і обґрунтування рішень |
| context | Початкові сторонні зміни baseline; sources із reference/access/result; assumptions |
| plan | steps, точні allowed_files, acceptance_criteria, test_plan |
| approval | Посилання на погодження і approved_files; у Planner порожні |
| changed_files | path, added/modified/deleted, reason; власні зміни, окремо від baseline |
| tests | reported_by, command, passed/failed/not_run, exit_code, фактичний result |
| remarks | id, P0–P3, evidence, recommendation, open/resolved |
| guardrails | Правило, compliant/violation/not_applicable/unverified, доказ |
| limitations | Недоступні джерела, невиконані перевірки та інші обмеження |

Для not_run exit_code=null, для виконаної команди — фактичний числовий код;
passed вимагає успішного результату й коду 0. Coder зберігає план Planner,
Reviewer — план і тестові докази Coder, додаючи власні перевірки.
На повторних етапах зберігай id зауважень і позначай виправлені resolved.

--output-schema задає структуру відповіді. ConvertFrom-Json перевіряє лише синтаксис,
не відповідність схемі. Оператор додатково перевіряє JSON Schema сумісним валідатором,
відповідність role/status, повноту критеріїв, згоду користувача та фактичні докази.
Схема сама не перевіряє достовірність дозволу, виконання тестів або зв'язок із diff.
Помилка CLI, відсутній/невалідний handoff чи суперечливий зміст зупиняють перехід.

Артефакти потрапляють тільки до нового artifacts/orchestration/<task_id>/;
не включай секрети. Кожен файл handoff зберігай окремо без перезапису попереднього.
Жодна роль не виконує stage, commit, push або sync_note. pass не скасовує цих меж.
