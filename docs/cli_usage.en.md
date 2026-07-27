> [简体中文](cli_usage.md) | **English**

# RuoYi Backend CLI Usage Guide

## 1. About This Document

This document describes the currently implemented CLI usage of `api`.

The unified command entry point is:

```bash
ruoyi <group> <command> [options]
```

The command groups currently implemented include:

- `app`
- `db`
- `ops`
- `cache`
- `job`
- `config`
- `crypto`
- `gen`
- `dev`
- `completion`
- `wizard`
- `tui`

## 2. Quick Start

### 2.1 Execution Directory

The `ruoyi` command must be run from the backend project root directory, i.e. the `api` directory.

```bash
cd api
ruoyi --help
```

### 2.2 Installing Dependencies

MySQL edition:

```bash
cd api
pip3 install -r requirements.txt
```

PostgreSQL edition:

```bash
cd api
pip3 install -r requirements-pg.txt
```

Notes:

- `requirements*.txt` already includes the project's own installation entry `.`, so there is no need to run `pip install -e .` separately.
- Once installation completes, `ruoyi` becomes available together with the current Python environment.

If you use Conda locally, it is recommended to activate the project environment before running the command:

```bash
conda activate ruoyi-fastapi
cd api
ruoyi --help
```

`textual` is already included in the existing dependency files, so once you install `requirements.txt` or `requirements-pg.txt` you can use the TUI directly.

### 2.3 Your First Command

Start the application in the development environment:

```bash
ruoyi app run --env=dev
```

The goal of this command is to be an equivalent replacement for:

```bash
python app.py --env=dev
```

## 3. Usage Rules

### 3.1 Position of Root Parameters

Root parameters must be placed before the command group.

Correct example:

```bash
ruoyi --color=never --icon=none ops health --env=dev
```

It is recommended not to write root parameters after the subcommand.

### 3.2 Environment Parameter

The CLI does not maintain a separate configuration system; it still reuses the project's original `config/env.py` parsing logic.

Common environment mappings are as follows:

- `--env=dev` -> `.env.dev`
- `--env=prod` -> `.env.prod`
- `--env=dockermy` -> `.env.dockermy`
- `--env=dockerpg` -> `.env.dockerpg`

### 3.3 Help Commands

You can view help level by level in the following ways:

```bash
ruoyi --help
ruoyi app --help
ruoyi app run --help
ruoyi db --help
ruoyi cache clear --help
```

### 3.4 Output Modes

Except for process-takeover commands such as `app run`, most commands support:

- `--output=text`
- `--output=json`

Recommended conventions:

- Prefer `text` for manual troubleshooting.
- Prefer `json` for script integration.
- Field names in `text` output uniformly use `snake_case`.
- Field names in `json` output keep a stable structured contract and are not renamed for display purposes.
- `json` output never mixes in color codes, emoji, or decorative text.
- `json` output never mixes in SQLAlchemy SQL logs, ordinary business logs, or other non-JSON text.
- `app run` takes over the application's foreground process directly, so it does not provide `--output`.

Examples:

```bash
ruoyi ops health --env=dev --output=text
ruoyi ops health --env=dev --output=json
```

### 3.5 Visual Options

The root command supports:

- `--color=auto|always|never`
- `--icon=emoji|ascii|none`

The current defaults are:

- `--color=always`
- `--icon=emoji`

Notes:

- These two parameters only affect `text` output.
- `json` output always keeps its structured result and is unaffected by color and icons.

Examples:

```bash
ruoyi --color=always ops server-info --env=dev
ruoyi --color=never ops server-info --env=dev
ruoyi --icon=none ops server-info --env=dev
```

### 3.6 Dangerous Commands

Commands that produce real side effects are placed under dangerous-command protection.

Dangerous commands fall into two categories:

- `high`: must support `--dry-run` or an equivalent preview capability.
- `normal`: requires confirmation by default, but does not mandate `--dry-run`.

The protection rules are as follows:

- In non-`prod` environments, confirmation is required by default.
- In a non-interactive terminal, if `--yes` is not passed, the command refuses to execute directly.
- In the `prod` environment, execution is disabled by default, and you must explicitly pass `--allow-prod --yes`.
- Only `high`-risk commands or commands that already implement a preview capability will offer `--dry-run`.

Examples:

```bash
ruoyi cache clear --env=dev --all --yes
ruoyi db upgrade --env=prod --revision=head --allow-prod --yes
ruoyi gen export sys_user --env=dev --mode=local --dry-run
```

## 4. Common Workflows

### 4.1 Local Development Startup

```bash
cd api
ruoyi app doctor --env=dev
ruoyi app run --env=dev
```

### 4.2 Pre-Release Checks

```bash
ruoyi ops health --env=prod --output=json
ruoyi ops server-info --env=prod
ruoyi db current --env=prod --output=json
```

### 4.3 Database Migration

```bash
ruoyi db check --env=dev
ruoyi db revision --env=dev --message="add user index" --yes
ruoyi db upgrade --env=dev --revision=head --yes
```

### 4.4 Cache and Scheduler Troubleshooting

```bash
ruoyi cache stats --env=dev
ruoyi cache keys sys_config --env=dev --output=json
ruoyi job list --env=dev --output=json
ruoyi job sync --env=dev --yes
```

### 4.5 Development-Time Checks

```bash
ruoyi dev lint cli --check-only
ruoyi dev test tests --keyword sanitize --maxfail=1 -q
```

### 4.6 Shell Completion Initialization

```bash
ruoyi completion doctor --output=json
ruoyi completion show bash
ruoyi completion install --activate
ruoyi completion install --shell=bash --activate
```

### 4.7 Interactive Wizard and TUI

```bash
ruoyi wizard app-run
ruoyi wizard db-upgrade
ruoyi wizard cache-clear
ruoyi wizard gen-export
ruoyi wizard gen-import
ruoyi wizard prod-check
ruoyi tui --env=dev
```

## 5. Command Quick Reference

### 5.1 `app`

Used to start the current FastAPI application, run pre-startup checks, take configuration snapshots, and inspect routes.

```bash
ruoyi app run --env=dev
ruoyi app doctor --env=dev --output=json
ruoyi app env --env=dev
ruoyi app config --env=dev --output=json
ruoyi app routes --env=dev
ruoyi app routes --env=dev --method=GET --path-prefix=/system
ruoyi app routes --env=dev --group-by=tag
ruoyi app routes --env=dev --include-hidden --output=json
```

### 5.2 `db`

Used for database connection checks and Alembic migration wrapping.

```bash
ruoyi db check --env=dev
ruoyi db current --env=dev --output=json
ruoyi db heads --env=dev --output=json
ruoyi db history --env=dev --limit=10
ruoyi db upgrade --env=dev
ruoyi db upgrade --env=dev --revision=head --dry-run
ruoyi db init --env=dev
ruoyi db downgrade --env=dev --revision=-1
ruoyi db downgrade --env=dev --revision=-1 --dry-run
ruoyi db revision --env=dev --message="add user index" --yes
ruoyi db revision --env=dev --message="sync table structure" --autogenerate --yes
```

### 5.3 `ops`

Used for basic operations checks.

```bash
ruoyi ops deps --env=dev
ruoyi ops ping-db --env=dev
ruoyi ops ping-redis --env=dev
ruoyi ops health --env=dev
ruoyi ops health --env=dev --output=json
ruoyi ops server-info --env=dev
ruoyi ops server-info --env=dev --output=json
```

Notes:

- `server-info --output=text` is suitable for manual inspection.
- `server-info --output=json` is better suited for script consumption.

### 5.4 `cache`

Used for cache statistics, querying, clearing, and warmup.

```bash
ruoyi cache stats --env=dev
ruoyi cache stats --env=dev --output=json
ruoyi cache keys login_tokens --env=dev --output=json
ruoyi cache get sys_config site.name --env=dev --output=json
ruoyi cache ttl sys_config site.name --env=dev --output=json
ruoyi cache clear --env=dev --cache-name=sys_config --yes
ruoyi cache clear --env=dev --cache-key=site.name --yes
ruoyi cache clear --env=dev --all --yes
ruoyi cache warmup --env=dev --yes
```

### 5.5 `job`

Used for querying, executing, and synchronizing scheduled jobs.

```bash
ruoyi job list --env=dev --output=json
ruoyi job list --env=dev --job-name=同步任务 --status=0 --paged
ruoyi job detail 1 --env=dev --output=json
ruoyi job logs --env=dev --output=json
ruoyi job logs --env=dev --job-name=同步任务 --status=1 --paged
ruoyi job run-once 1 --env=dev --yes
ruoyi job pause 1 --env=dev --yes
ruoyi job resume 1 --env=dev --yes
ruoyi job sync --env=dev --yes
ruoyi job run-once 1 --env=prod --allow-prod --yes
```

### 5.6 `config`

Used for reading, writing, and cache-synchronizing system parameter configurations.

```bash
ruoyi config list --env=dev --output=json
ruoyi config list --env=dev --paged
ruoyi config get <config-key> --env=dev --output=json
ruoyi config get <config-key> --env=dev --source=both --output=json
ruoyi config get <config-key> --env=dev --source=db --output=json
ruoyi config get <config-key> --env=dev --source=cache
ruoyi config doctor --env=dev --output=json
ruoyi config set sys.user.initPassword --env=dev --value=123456 --name="初始密码" --yes
ruoyi config set sys.user.initPassword --env=dev --value=123456 --remark="CLI update" --yes
ruoyi config sync-cache --env=dev --yes
```

Notes:

- `config get --source=both` reads from both the database and Redis, and returns `database`, `cache`, and `inSync` in the JSON.
- `config get --source=db` reads only from the parameter configuration table, suitable for confirming the actual stored value in the database.
- `config get --source=cache` reads only from the Redis cache, suitable for confirming the value currently hit at runtime.
- If a key exists only in the cache and not in the database, `--source=db` returns "parameter configuration does not exist", which means there is no corresponding record on the database side and does not indicate an abnormal cache read.

### 5.7 `crypto`

Used for validating transport encryption configuration, exporting public keys, and key-related helper operations.

```bash
ruoyi crypto validate --env=dev --output=json
ruoyi crypto keygen --env=dev --kid=default --key-size=2048
ruoyi crypto keygen --env=dev --output=json --kid=default --key-size=2048
ruoyi crypto export-public --env=dev
ruoyi crypto export-public --env=dev --output=json
ruoyi crypto rotate --env=dev --output=json --next-kid=v2 --key-size=2048 --yes
```

Notes:

- `crypto keygen` outputs the newly generated public key, private key, and the recommended `envPatch` to write.
- `crypto rotate` currently only generates rotation helper results and does not directly rewrite the `.env.*` files.
- Output involving private keys is recommended only in a secure terminal.

### 5.8 `gen`

Used for querying code-generation business tables, importing, creating tables, previewing, and exporting.

```bash
ruoyi gen list --env=dev --output=json
ruoyi gen db-list --env=dev --output=json
ruoyi gen detail 1 --env=dev --output=json
ruoyi gen import-table sys_user sys_role --env=dev --yes
ruoyi gen import-table sys_user sys_role --env=dev --dry-run
ruoyi gen create-table --env=dev --sql="create table demo_test (id bigint primary key)" --yes
ruoyi gen create-table --env=dev --sql-file=./sql/demo.sql --dry-run
ruoyi gen preview 1 --env=dev
ruoyi gen preview 1 --env=dev --output=json
ruoyi gen export sys_user --env=dev --yes
ruoyi gen export sys_user sys_role --env=dev --mode=zip --output-file=./build/gen.zip --yes
ruoyi gen export sys_user --env=dev --mode=local --dry-run
ruoyi gen sync-db sys_user --env=dev --yes
```

Notes:

- `import-table` and `create-table` support `--dry-run`.
- `create-table` must be passed exactly one of `--sql` or `--sql-file`, and only one.
- `gen preview --output=text` displays the preview code content in blocks by template.
- `export --mode=local` reuses the existing generation logic and respects `GenConfig.allow_overwrite`.

### 5.9 `dev`

Used for development-time code checks and test execution.

```bash
ruoyi dev lint
ruoyi dev lint cli tests --check-only
ruoyi dev lint cli --fix
ruoyi dev lint cli --output=json
ruoyi dev test
ruoyi dev test tests/test_log_sanitize_util.py
ruoyi dev test tests --keyword sanitize --maxfail=1 -q
ruoyi dev test tests --output=json
```

Notes:

- `dev lint` runs `ruff format` first and then `ruff check` by default.
- `--check-only` switches to check-only mode, without writing back.
- `--fix` runs `ruff check --fix`.
- `dev test` runs tests via the current environment's `python -m pytest`.

### 5.10 `completion`

Used to generate, install, and diagnose shell completion.

```bash
ruoyi completion doctor --output=json
ruoyi completion show bash
ruoyi completion show zsh
ruoyi completion show fish
ruoyi completion show powershell
ruoyi completion install --activate
ruoyi completion install --shell=bash
ruoyi completion install --shell=zsh --activate
ruoyi completion install --shell=fish
ruoyi completion install --shell=powershell --activate
```

Notes:

- The current version already supports `bash`, `zsh`, `fish`, and `powershell`.
- When `--shell` is not passed, `install` prefers to auto-detect the current shell.
- `install` writes to the default script location corresponding to the shell by default.
- For Bash and Zsh, if auto-loading is desired, it is recommended to combine it with `--activate`.
- For PowerShell, if auto-loading is desired, it is recommended to combine it with `--activate`.
- The Bash script has been made compatible with older versions of Bash; if you have previously installed the script, please run `ruoyi completion install --activate` once more.
- `completion doctor` provides a recommended install command and source suggestion.
- The context completions currently added include `--env`, `cache_name`, `cache_key`, `config_key`, `db --revision`, `gen` business table names, `gen` database table names, `gen --sql-file`, `gen --output-file`, `job_name`, and `job_id`.

### 5.11 `wizard`

Used to interactively assemble dangerous or complex commands and output a preview before actually executing them.

```bash
ruoyi wizard app-run
ruoyi wizard db-upgrade --default-env=dev --default-revision=head
ruoyi wizard cache-clear --default-env=dev --default-mode=cache-name
ruoyi wizard gen-export --default-env=dev --default-mode=zip
ruoyi wizard gen-import --default-env=dev --default-table-names=sys_notice
ruoyi wizard prod-check --default-env=prod
```

Notes:

- All wizards first collect input, then output a preview summary along with the final CLI command that will be executed.
- `db-upgrade`, `cache-clear`, `gen-export`, and `gen-import` all support running a `dry-run` first by default.
- A wizard is essentially still a wrapper around the underlying CLI; its final return value, exit code, and dangerous-command protection rules remain consistent with the underlying commands.

### 5.12 `tui`

Used to enter a read-only inspection workbench, browsing application, operations, database, cache, job, code generation, parameter configuration, and encryption status in a page-based manner.

```bash
ruoyi tui --env=dev
ruoyi tui --env=prod
```

Notes:

- The current TUI is a read-only inspection workbench; write-operation entry points within pages require a secondary confirmation via a confirmation dialog or wizard.
- The page-switching shortcuts are `D/A/O/B/C/T/G/P/E`, corresponding to Overview, Application, Operations, Database, Cache, Job, Code Generation, Parameter Configuration, and Encryption respectively.
- Common shortcuts include `R` to refresh, `Q` to quit, `S` to focus the sidebar, `←/→` to switch focus or area, `J/K` to scroll, `PgUp/PgDn` to page, and `Home/End` to jump to the start/end.
- If the current Python environment lacks the TUI dependencies, `ruoyi tui` returns a failure result and prompts you to re-run `pip install -r requirements.txt` or `pip install -r requirements-pg.txt`.

## 6. List of Dangerous Commands

The commands currently under protection include:

- `cache clear`
- `cache warmup`
- `db upgrade`
- `db init`
- `db downgrade`
- `db revision`
- `config set`
- `config sync-cache`
- `crypto rotate`
- `job run-once`
- `job pause`
- `job resume`
- `job sync`
- `gen import-table`
- `gen create-table`
- `gen export`
- `gen sync-db`

Notes:

- In the `prod` environment, these commands refuse to execute by default.
- In non-`prod` environments, these commands also enter interactive confirmation by default.
- In a non-interactive terminal, if `--yes` is not passed, the command refuses to execute directly.
- If a command supports `--dry-run`, prefer running a preview once first.

## 7. Output and Exit Codes

### 7.1 Output Format

The CLI supports two output formats:

- `text`
- `json`

Field naming conventions:

- `text` output is primarily aimed at human reading, and field names uniformly use `snake_case`.
- `json` output is primarily aimed at script consumption, and field names keep the command contract definition and do not change for visual optimization.

Example:

```bash
ruoyi ops health --env=dev --output=json
```

Standard samples:

Text output sample:

Command:

```bash
ruoyi --color=never --icon=none app config --env=dev
```

Output:

```text
OK SUCCESS
env: dev
application:
  name: RuoYi-FastAPI
  host: 0.0.0.0:9099
  root_path: /dev-api
  reload: true
  workers: 1
  disable_swagger: false
  disable_redoc: false
database:
  type: mysql
  host: 127.0.0.1:3306
  name: ruoyi-fastapi
redis:
  host: 127.0.0.1:6379
logging:
  level: INFO
transport_crypto:
  enabled: false
  mode: off
```

JSON output sample:

Command:

```bash
ruoyi app config --env=dev --output=json
```

Output:

```json
{
  "ok": true,
  "env": "dev",
  "config": {
    "env": "dev",
    "name": "RuoYi-FastAPI",
    "host": "0.0.0.0",
    "port": 9099,
    "rootPath": "/dev-api",
    "reload": true,
    "workers": 1,
    "disableSwagger": false,
    "disableRedoc": false,
    "dbType": "mysql",
    "dbHost": "127.0.0.1",
    "dbPort": 3306,
    "dbDatabase": "ruoyi-fastapi",
    "redisHost": "127.0.0.1",
    "redisPort": 6379,
    "logLevel": "INFO",
    "transportCryptoEnabled": false,
    "transportCryptoMode": "off"
  }
}
```

Dangerous-command refusal sample:

Command:

```bash
ruoyi db revision --env=prod --message="doc-sample" --output=json
```

Output:

```json
{
  "ok": false,
  "message": "生产环境默认禁止直接执行危险命令：db revision",
  "hint": "如确认执行，请传入 --allow-prod；如需跳过确认，请同时传入 --yes"
}
```

`dry-run` output sample:

Command:

```bash
ruoyi db upgrade --env=dev --revision=head --dry-run --yes --output=json
```

Output:

```json
{
  "ok": true,
  "message": "数据库已升级到 head（dry-run）",
  "dryRun": true,
  "command": [
    "alembic",
    "-c",
    "/path/to/api/alembic.ini",
    "upgrade",
    "head"
  ],
  "cwd": "/path/to/api"
}
```

Code-generation `dry-run` text sample:

Command:

```bash
ruoyi --color=never --icon=none gen export demo_table --env=dev --dry-run --yes --output=text
```

Output:

```text
OK SUCCESS
env: dev
mode: zip
dry_run: true
message: 代码导出演练完成，未执行实际导出
table_names:
  - demo_table
output_file: /path/to/api/gen_code_demo_table.zip
```

Code-generation `dry-run` JSON sample:

Command:

```bash
ruoyi gen create-table --env=dev --dry-run --yes --sql='CREATE TABLE demo_cli_test (id bigint);' --output=json
```

Output:

```json
{
  "ok": true,
  "message": "建表语句演练完成，未执行实际建表",
  "dryRun": true,
  "statementCount": 1,
  "tableNames": [
    "demo_cli_test"
  ],
  "sql": "CREATE TABLE demo_cli_test (id bigint);",
  "env": "dev"
}
```

Parameter error sample:

Command:

```bash
ruoyi --color=never --icon=none gen create-table --env=dev --dry-run --yes --sql='DROP TABLE demo_cli_test;' --output=text
```

Output:

```text
FAIL FAILED
message: 创建表结构失败
error: 建表语句不合法，仅允许 CREATE TABLE 语句
env: dev
```

Parameter error JSON sample:

Command:

```bash
ruoyi gen create-table --env=dev --dry-run --yes --sql='DROP TABLE demo_cli_test;' --output=json
```

Output:

```json
{
  "ok": false,
  "message": "创建表结构失败",
  "error": "建表语句不合法，仅允许 CREATE TABLE 语句",
  "env": "dev"
}
```

Dependency-check failure sample:

Notes:

- The results returned by `app doctor` and `ops health` are affected by the connectivity of the current database and Redis.
- If a dependency is unavailable, the command outputs a failure result and returns exit code `10`.

Command:

```bash
ruoyi --color=never --icon=none app doctor --env=dev --output=text
```

Output:

```text
FAIL FAILED
env: dev
checks:
  database: false | 数据库连接失败 | error: <database error message>
  redis: false | Redis连接失败 | error: <redis error message>
  crypto: true | 传输加密配置校验通过
```

Command:

```bash
ruoyi ops health --env=dev --output=json
```

Output:

```json
{
  "env": "dev",
  "database": {
    "ok": false,
    "message": "数据库连接失败",
    "error": "<database error message>",
    "exit_code": 20
  },
  "redis": {
    "ok": false,
    "message": "Redis连接失败",
    "error": "<redis error message>",
    "exit_code": 21
  },
  "ok": false
}
```

### 7.2 Exit Codes

The current unified exit codes are as follows:

- `0`: success
- `2`: parameter error
- `10`: dependency check failed
- `20`: database failed
- `21`: Redis failed
- `22`: scheduler failed
- `30`: dangerous operation refused
- `50`: uncategorized runtime error

## 8. FAQ

### 8.1 The `ruoyi` command is unavailable

Please confirm the following in order:

- Whether the current directory is `api`.
- Whether the current Python environment has run `pip install -r requirements.txt` or `pip install -r requirements-pg.txt`.
- Whether the current terminal is actually using the same Python/Conda environment where the dependencies were installed.

### 8.2 The command reports a database or Redis connection failure

Please check:

- Whether the database configuration in `.env.*` is correct.
- Whether the Redis configuration in `.env.*` is correct.
- Whether the current network, container, or host allows connecting to the target service.
- `app doctor` and `ops health` return exit code `10` when a dependency is abnormal.
- A single dependency failure carries the original `error` and the corresponding dependency exit code in the JSON.

### 8.3 The text output is too fancy or unsuitable for script processing

You can directly switch the output and visual parameters:

```bash
ruoyi --color=never --icon=none ops health --env=dev --output=text
ruoyi ops health --env=dev --output=json
```

### 8.4 The usage documentation is inconsistent with the implementation

The current CLI implementation and the command help output should be taken as authoritative, and this document should be updated accordingly.
