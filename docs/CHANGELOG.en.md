> [简体中文](CHANGELOG.md) | **English**

# Changelog

> Below is the changelog of the upstream RuoYi-Vue3-FastAPI; ezdata's own changes are recorded in this section.

## ezdata (v2.0)

### Added
- **Agent Skills (Claude Skills-like)** `module_ai`: a capability pack = name + description + `SKILL.md` body + attached files (may include directories) + soft references to other skills; **progressive disclosure** — the skill directory is always resident (L1), `load_skill` pulls the body (L2), `read_skill_file` pulls attached files (L3); split into **process-type** (globally resident manifest) / **knowledge-type** (bound to a data source, surfaced via `search_datasource_knowledge` when the source is identified). Full-screen IDE editor (file tree + Monaco + import folder/zip + export zip). Built-in skills `chart_building`/`es_query`/`task_scheduling`; apps can bind skills. Table `ai_skill`, menu/permission `ai:skill:*`.
- **Data catalog retrieval narrowing** `module_ai/tools/catalog_index`: embeds `data_model` (tables) into a dedicated ES index (reusing `module_rag`'s vector store), and during conversation retrieves the Top-K relevant tables for the question to inject into the system prompt, replacing the full catalog — the resident footprint is independent of the total table count (obvious token savings for large stores, and no more missing tables due to per-source truncation); for small stores it automatically falls back to the full catalog. `data_model` create/update/delete **incrementally syncs** the index + a "Sync Index" button in data source management (async `module_data.sync_catalog_index` on a Celery worker).
- **Agent context/tools/results slimming**: trim the always-resident instructions of the data agent, move conditional topic-specific content into built-in skills; `task_propose` is **conditionally mounted** by task intent (tool schema for a pure data-query turn is reduced by ~73%); trim tool docstrings; cap the sandbox `stdout` result; `search_datasource_knowledge` only attaches business context when the knowledge base has a hit; Anthropic **prompt caching** (`cache_system_prompt`/`cache_tools`, effective on direct connections / gateways that support caching).
- **Finance demo enhancements**: **A-share market overview multi-chart dashboard**; A-share daily bars changed to two tasks — "scheduled incremental snapshot of the first page + one-time full backfill" — sharing the same index/model `fin_stock_daily` (dedup by md5(symbol+date), removing the original six fixed-symbol tasks); merged into `demo_seed.py` (28 data-integration tasks / 27 data models).
- **Lightweight query UI** `ezdata/interface/web`: a minimal, standalone tool isolated from the platform (standard-library http.server + sqlite connection catalog + agno LLM), for data source management / browsing table fields / native & AI data fetching / Excel export. The AI "Generate Query" flow changed to generate-only → preview → apply manually → click Query to execute.
- **AI goes through agno**: currently supports the openai (including OpenAI-compatible endpoints) and anthropic families, with lazy imports that do not pollute the core.
- **Task timeout (prevents hangs and blocking)**: Celery global soft/hard timeouts (`CELERY_TASK_SOFT_TIME_LIMIT`/`CELERY_TASK_TIME_LIMIT`, default 1800/2100) + task-level `timeout` (0 = default / -1 = unlimited / >0 = custom) + `worker_prefetch_multiplier=1`; a hard timeout SIGKILLs to release the slot, a soft timeout warns without retrying.
- **Restart scheduler**: a "Restart Scheduler" button on the System Monitor - Scheduled Tasks page (super admin; permission `monitor:job:restart`), which does close → re-acquire lock → reload all tasks; across multiple workers it is executed by the leader via a Redis channel broadcast.

### Fixed / Optimized
- **Internal AI generation (ETL data fetching/transformation, data query) now prefers the system fallback model (`LLM_*`)**: these entry points have no model-selection UI, and no longer pick an enabled model from the store, avoiding being dragged down by a model whose key is not configured (fixing errors like `AIMLAPI_API_KEY not set`); a friendly prompt is shown when an enabled model has an empty key.
- Testing the connection while editing a data source no longer fails because the secret is left blank (`/api/test` passes name to merge onto the original connection as the base).

### Upgrade Notes
- An existing database (initialized from `*.sql`, not under alembic control) needs the `task.timeout` column added: `alembic stamp 0002_seed_system && alembic upgrade head`, or manually `ALTER TABLE task ADD COLUMN timeout INT NULL DEFAULT 0`. See `docs/DEPLOY.md` §9.5 for details.

## RuoYi-Vue3-FastAPI v1.9.0

### Dependencies

Both frontend and backend dependencies have been upgraded; please upgrade dependencies or recreate the environment.

### New Features

1. Added AI management module ([#69](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/69)).
2. Added mobile module ([#73](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/73)).
3. Added multi-worker running support ([#76](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/76)).
4. Added demo mode to the app ([#78](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/78)).

### Bug Fixes

1. Fixed the exception with the query_db parameter in the delete interface of the code-generation controller template ([#63](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/63)).
2. Fixed the incorrect response_model declaration in the login interface ([#71](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/71)).
3. Fixed the issue where the API docs could not be accessed directly via the backend address ([#74](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/74)).
4. Fixed the issue of create_app being executed repeatedly ([#84](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/84)).

### Refactoring

1. Removed support for python3.9 ([#67](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/67)).

### Code Optimization

1. Optimized alembic's table-model handling logic to avoid interference from unrelated tables ([#68](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/68)).
2. Optimized the code-generation backend template ([#72](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/72)).
3. Throw an exception when automatic route registration fails, to ease debugging ([#79](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/79)).
4. Optimized the tooltip descriptions of some page fields (#80).
5. Optimized project startup speed ([#82](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/82)).
6. Optimized the dark-mode toggle effect ([#83](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/83)).
7. Optimized the scheduler's task-state synchronization mechanism under hot-reload mode or a single worker ([#85](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/85)).
8. Made the anti-duplicate-submission interval customizable ([#87](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/87)).
9. Optimized the captcha computation result to be non-negative ([#88](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/88)).
10. Optimized CI test stability ([#90](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/90)).

## RuoYi-Vue3-FastAPI v1.8.1

### New Features

1. Added E2E tests ([#57](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/57)).

### Bug Fixes

1. Fixed the DictTag component rendering exception ([#59](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/59)).

### Code Optimization

1. Optimized data-permission dependencies ([#55](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/55)).
2. Dynamically import scheduled-task functions, removing eval ([#56](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/56)).
3. Optimized the docker compose configuration file for the pg version ([#61](https://github.com/insistence/RuoYi-Vue3-FastAPI/pull/61)).

## RuoYi-Vue3-FastAPI v1.8.0

### Dependencies

#### Backend

1. Backend dependencies upgraded to the latest versions; please upgrade dependencies or recreate the environment.

### New Features

1. Added a request context management class.
2. Added the `PreAuthDependency`, `CurrentUserDependency`, `DataScopeDependency`, `DBSessionDependency`, `UserInterfaceAuthDependency`, and `RoleInterfaceAuthDependency` dependency functions.
3. Added a context-cleanup middleware.
4. Added a common vo module.
5. Added a method for configuring documentation static resources.
6. Added an automatic route-registration feature.
7. Added a docker compose deployment method.
8. Menu navigation settings now support top-only.

### Bug Fixes

1. Fixed the issue where the force-logout feature was ineffective under single-account login mode [#52](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/52).
2. Ensured the ApschedulerJobs field types match the field types of the table created by apscheduler by default [#53](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/53).
3. Fixed the issue where service monitoring could not run properly when a disk was abnormal.
4. Removed the foreign key of the code-generation business table, fixing the inability to delete.
5. Fixed the navbar offset that appeared when the header was fixed.
6. Fixed the blank issue when switching routes back after removing all controls in the form builder.
7. Fixed the error when clearing after selecting "between" on the time control in the code-generation v3 template.

### Refactoring

1. Enhanced ruff rules and improved type hints.
2. Optimized the project structure, added a common module, and moved the original annotation, aspect, constant, and enums modules under the common module.
3. Refactored the app and server design.

### Code Optimization

1. The controller layer now uses the new dependencies throughout.
2. Current-user information now uses context variables.
3. The pagination model now uses PageModel from the common vo module.
4. Optimized the response-model display in the API docs.
5. The operation response model now uses CrudResponseModel from the common vo module.
6. Optimized the interface-description information in the API docs.
7. The copyright info at the bottom of the login/register pages now reads from configuration.
8. Optimized the zip filename for downloading generated code.
9. Destroy the clone plugin when closing the form builder tab.
10. Inline forms now default to a fixed width.
11. Optimized the display of detailed request parameters in operation logs.
12. Optimized the index page title to read from configuration.
13. Optimized the numeric-type value handling logic of the dictionary component.
14. Optimized the loose matching of dictionary-component values.
15. Header is now fixed by default.

## RuoYi-Vue3-FastAPI v1.7.1

### Dependencies

1. Backend dependencies remove passlib and use bcrypt directly.

### Bug Fixes

1. Fixed the issue of abnormally generated fields in the edit interface of the code-generation controller template.
2. Removed passlib and used bcrypt directly to fix the password-verification exception [#48](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/48) [#49](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/49).

### Code Optimization

1. Added the table description to the code-generation do template.

## RuoYi-Vue3-FastAPI v1.7.0

### Dependencies

1. Frontend and backend dependencies upgraded; please upgrade dependencies or recreate the environment.

### New Features

1. Added alembic support.
2. File & image upload components support custom addresses & parameters.
3. Added a default packaging configuration item.
4. The show/hide-columns component supports select-all / deselect-all.
5. openPage for adding tabs supports passing parameters.
6. Mask message prompt while an external link loads.
7. Added a drag-to-sort property to the upload component.
8. Added a disabled property to the image upload component.
9. Code-generation columns support drag-to-sort.
10. Added a default initialization password for users.
11. Added a toggle for displaying tab icons.
12. Added bottom copyright info and a toggle.
13. Added clearing for the user's belonging department.
14. Added validation prompts to user import.
15. Menu search supports keyboard selection & a hover-theme background.
16. Added the SQLAlchemy model class corresponding to the apscheduler_jobs table.
17. Initial password supports a custom modification policy.
18. Account passwords support a custom update cycle.
19. Set the default last-password-update time when registering an account.
20. Display-column info supports object format.

### Bug Fixes

1. Fixed the issue where the logout interface did not dynamically judge according to the app_same_time_login config item [#IBZZ1S](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/IBZZ1S).
2. Fixed the issue where, when the upload component was referenced multiple times, dragging was only effective for the first one.

### Code Optimization

1. Optimized interface time-cost calculation.
2. Optimized the startup-information display.
3. Optimized the frontend route-handling function code.
4. The login and register page headers use the VITE_APP_BASE_API config value.
5. Optimized so that a disabled role cannot be assigned.
6. Optimized the rich-text console warning exception.
7. Optimized the deprecated checkbox API.
8. Optimized the display of the nickname & settings in the navbar.

### Refactoring

1. Refactored IP-region lookup into an async call.
2. Adjusted do and sql to adapt to each other to support alembic.
3. Rich-text copy-paste images are uploaded to a url.

## RuoYi-Vue3-FastAPI v1.6.2

### New Features

1. Added a disabled property to the file upload component.
2. Added types to the file upload component.

### Bug Fixes

1. Fixed the error in the time query of log management [#27](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/27).
2. Fixed the issue where executing a single task while the scheduled task status was paused would trigger the cron expression [#31](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/31).
3. Fixed the dict_code exception when modifying a dictionary type.
4. Fixed the abnormal dictionary-data update time when modifying a dictionary type.
5. Fixed the time-query issue in code-generation templates [#28](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/28).
6. Fixed the missing department name in user export.

### Code Optimization

1. Optimized the field display and rendering when adding and editing in code generation.
2. Changed pagination to a flex layout.
3. Optimized the code-generation vue template [#23](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/23).

## RuoYi-Vue3-FastAPI v1.6.1

### Dependencies

#### Backend

1. Added the sqlglot dependency

```bash
pip install sqlglot[rs]==26.6.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Bug Fixes

1. Introduced sqlglot to fix the SQL-statement parsing exception.
2. Fixed the judgment exception in the dao-layer template for code-generation field uniqueness validation.
3. Introduced generics to fix the loss of model docs decorated by as_query and as_form.
4. Fixed the possible missing NotBlank in the code-generation master-detail vo template.

## RuoYi-Vue3-FastAPI v1.6.0

### Dependencies

1. Backend dependencies upgraded to the latest versions; please upgrade dependencies or recreate the environment.

### New Features

1. Added the code-generation feature, which supports one-click generation and download of frontend and backend code by configuring database table information; the sql file needs to be re-executed, so please back up your data first.
2. Added the form-builder feature.
3. User avatars now support http(s) links.
4. Added trace middleware to strengthen log-chain tracing and response headers [@y1ren](https://gitee.com/y1ren).
5. User management supports column-split dragging.
6. Menu breadcrumb navigation supports multi-level display.
7. The whitelist supports wildcard path matching.
8. Supports enabling dark mode.

### Bug Fixes

1. Fixed the issue where inner-link pages could not open when Tags-Views was closed by default.
2. Fixed the ineffective interception when deleting the currently logged-in user.
3. Fixed the incomplete string-rule validation of the scheduled-task target.
4. Fixed the issue where executing a single task would overwrite an already-enabled task [#IBEKD2](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/IBEKD2).
5. Fixed the failure of changing a password with special characters in the personal center.

### Code Optimization

1. Optimized the export method.
2. Changed parameter key-values to multi-line text.
3. Optimized the display of the operation method in logs.
4. Optimized the way the log decorator obtains core parameters.
5. User management filters out disabled departments.
6. Fixed the missing highlight when clicking a TopNav inner-link menu.
7. ResponseUtil supplemented with complete parameters.

## RuoYi-Vue3-FastAPI v1.5.1

### New Features

1. Scheduled tasks now support calling async functions.

### Code Optimization

1. Optimized the dictionary-array condition judgment.
2. Validate whether the filename contains special characters.
3. Removed the deprecated log_decorator decorator.

## RuoYi-Vue3-FastAPI v1.5.0

### New Features

1. Added support for the PostgreSQL database.

### Bug Fixes

1. Fixed the issue where the DictTag component threw an exception in the console [#IAYSVZ](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/IAYSVZ).
2. Fixed the incorrect filename of the exported login log.

### Code Rollback

1. Because of an underlying bug in fastapi's query-parameter model, rolled back the query-parameter model declaration to as_query.

### Code Optimization

1. Optimized CamelCaseUtil and SnakeCaseUtil to be compatible with more conversion scenarios.
2. Optimized the sorting of list queries.
3. Optimized the parameter-settings page.
4. Optimized so that no prefix is added when an uploaded image already carries a domain.

## RuoYi-Vue3-FastAPI v1.4.0

### Dependencies

#### Backend

1. Updated the fastapi version to 0.115.0

```bash
pip install fastapi[all]==0.115.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Refactoring

1. Based on the new features of fastapi 0.115.0, directly use pydantic models to receive query parameters and form data, removing the original as_query and as_form usage.

### Bug Fixes

1. Fixed a coding error in the role-management service.

### Code Optimization

1. Optimized the frontend login request method.

## RuoYi-Vue3-FastAPI v1.3.3

### Dependencies

#### Backend

1. Updated the pydantic-validation-decorator version to 0.1.4, fixing some underlying bugs.

### Bug Fixes

1. Fixed the ineffective conditional query in the online-user module.

### Code Optimization

1. Optimized the consistency of frontend and backend field descriptions in the online-user module.
2. Added logger printing for exception handling in the log decorator.

## RuoYi-Vue3-FastAPI v1.3.2

### New Features

1. Added gzip compression middleware.

### Bug Fixes

1. Fixed the error in the pagination function's calculation of has_next [#10](https://github.com/insistence/RuoYi-Vue3-FastAPI/issues/10).
2. Fixed the error in the scheduled-task listener function where the event had no job_id.

### Code Optimization

1. Optimized the comments of the add-middleware function.

## RuoYi-Vue3-FastAPI v1.3.1

### Bug Fixes

1. Fixed the issue where the log decorator could not record exception logs after the new exception-handling mechanism was adopted in version 1.3.0.

### Code Optimization

1. Supplemented the scheduled-task illegal strings.

## RuoYi-Vue3-FastAPI v1.3.0

### Dependencies

1. Both frontend and backend dependencies upgraded to the latest versions; please upgrade dependencies or recreate the environment.
2. Replaced `python-jose` with `PyJWT` to resolve some security issues.

### New Features

1. Added a field-validation decorator that supports manually triggering validation, packaged as the `pydantic-validation-decorator` library.
2. Added field-uniqueness validation to the `service` layer of each module.
3. Added the global `ServiceException` custom service exception and `ServiceWarning` custom service warning, eliminating the need to write large amounts of exception handling in interfaces.
4. Added a route name to menu management; please execute the following sql to add the field to the database:

```sql
ALTER TABLE sys_menu ADD COLUMN route_name varchar(50) DEFAULT '';
```

5. Added `constant` constant configuration and `enums` enum-type configuration.
6. Added the `StringUtil` and `CronUtil` utility classes.

### Bug Fixes

1. Fixed privilege-escalation vulnerabilities in user management, role management, and department management.
2. Fixed the issue where the `status` and `del_flag` types in the `dao` layer of each module were inconsistent with the database.
3. Fixed the issue where the left-side menu could not display on mobile.
4. Fixed other known BUGs.

### Refactoring

1. Refactored the log decorator to `Log`; the `log_decorator` decorator will be removed in a future version, so please migrate as soon as possible.
2. Refactored `RedisInitKeyConfig` into an enum type; you can now obtain the corresponding `key` and `remark` via
`RedisInitKeyConfig.ACCESS_TOKEN.key` and `RedisInitKeyConfig.ACCESS_TOKEN.remark`.
3. Refactored the data-permission logic with underlying optimizations; usage remains the same as before.

### Code Optimization

1. Introduced `ruff` to format, detect, and fix the backend code and optimize imports.
2. Each module optimized its exception-handling logic based on the `ServiceException` custom service exception and `ServiceWarning` custom service warning.
3. The `vo` layer of each module uses `Field` to declare fields.
4. Optimized the field-description display in the API docs.

## RuoYi-Vue3-FastAPI v1.2.2

### Bug Fixes

1. Fixed the issue where the task in scheduling was not removed when deleting a scheduled task.
2. Fixed the component conditional-judgment error when the menu generates routes.

## RuoYi-Vue3-FastAPI v1.2.1

### Bug Fixes

1. Fixed the abnormal creation-time record when adding data in each module.
2. Fixed a series of related issues such as abnormal route loading when a menu is mounted to the root directory.

### Code & Performance Optimization

1. Changed the proxy localhost to 127.0.0.1 to accommodate the abnormal localhost resolution on some devices.

## RuoYi-Vue3-FastAPI v1.2.0

### Important Notice

This update is a **_breaking update_**; it refactors the database orm to be async, with major code changes, so please upgrade with caution.
1. The original Session type declarations are uniformly changed to AsyncSession.
2. The functions of the service layer and dao layer are changed to async functions; please call them with await.
3. orm queries no longer support query; please use statements such as select, update, delete. For specific usage, refer to [https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html](https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html).

### Dependencies

#### Backend

1. Added the asyncmy dependency to support async orm operations on mysql; please reinstall dependencies

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple。
```

### New Features

1. Added the SnakeCaseUtil utility class, migrating the camel_to_snake function from the original CamelCaseUtil utility class to the SnakeCaseUtil utility class.

### Bug Fixes

1. Fixed the issue where resetting a user's password in the user-management module would abnormally reset the user's post and role.
2. Fixed the exception when clearing scheduled-task logs.

## RuoYi-Vue3-FastAPI v1.1.3

### New Features

1. Added illegal-character validation to user passwords.

### Bug Fixes

1. Fixed the inconsistency between frontend and backend fields in the notice-announcement list query.
2. Fixed the backend exception after modifying basic profile info in the personal center.

## RuoYi-Vue3-FastAPI v1.1.2

### New Features

1. Added database connection-pool related configuration to the config file.

### Bug Fixes

1. Fixed the backend exception after changing the password in the personal center.

### Code & Performance Optimization

1. Used @lru_cache to cache IP-region lookup results, avoiding repeated calls to the IP-region lookup interface to optimize performance.

## RuoYi-Vue3-FastAPI v1.1.1

### Bug Fixes

1. Fixed the issue where updated info was not synced to the scheduler when editing a scheduled task [#I9EK56](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I9EK56).
2. Fixed the backend exception when editing a role's data permissions [#I9ENQN](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I9ENQN).
3. Fixed the issue where menu-configured route parameters did not take effect.
4. Fixed the issue where menu sorting did not take effect when obtaining route information.
5. Fixed the abnormal echo of the is-external-link and is-cache fields when adding a menu.

## RuoYi-Vue3-FastAPI v1.1.0

### New Features

1. Added a sqlalchemy logging switch configuration to the backend config file.
2. Added an IP-region lookup switch configuration to the backend config file.
3. Added an account-simultaneous-login switch configuration to the backend config file.

### Bug Fixes

1. Fixed the exception in the logout interface when the token itself was expired [#I9CBWT](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I9CBWT).
2. Fixed the login exception when the system version number or browser version number could not be obtained [#I9CYNM](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I9CYNM).

## RuoYi-Vue3-FastAPI v1.0.3

### New Features

1. Added IP-blacklist validation to account-password login.

### Bug Fixes

1. Fixed the issue where external-link menus could not open [#I95KBK](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I95KBK).
2. Fixed the abnormal echo of the is-cache and is-external-link fields on the add-and-edit-menu pages [#I95KBK](https://gitee.com/insistence2022/RuoYi-Vue3-FastAPI/issues/I95KBK).

## RuoYi-Vue3-FastAPI v1.0.2

### New Features

1. Added list parameter reception to the user interface permission validation, enabling the same interface to support validation of multiple permission identifiers.
2. Added a dependency for validating interface permissions by role

### Bug Fixes

1. Fixed the data-permission exception in the user-management and department-management modules.

### Code & Performance Optimization

1. Adjusted the interface permission identifiers of some interfaces in the parameter-settings, department-management, dictionary-management, scheduled-task, log-management, role-management, and menu-management modules.

## RuoYi-Vue3-FastAPI v1.0.1

### Dependencies

#### Backend

1. Updated the fastapi version to 0.109.1 to fix some security issues; command:

```bash
pip install fastapi[all]==0.109.1 -i https://mirrors.aliyun.com/pypi/simple/
```

### New Features

1. Added field-sorting query to the log-management module.

## RuoYi-Vue3-FastAPI v1.0.0

The first version of RuoYi-Vue3-FastAPI is released!
The features of this version are as follows:
1. User management: Users are the operators of the system; this feature mainly completes the configuration of system users.
2. Role management: Assignment of role-menu permissions.
3. Menu management: Configure system menus, operation permissions, button permission identifiers, etc.
4. Department management: Configure the system organization (company, department, group).
5. Post management: Configure the positions held by system users.
6. Dictionary management: Maintain some relatively fixed data frequently used in the system.
7. Parameter management: Dynamically configure common parameters for the system.
8. Notice announcement: Publish and maintain system notice-announcement information.
9. Operation log: Record and query normal system operation logs; record and query system exception information logs.
10. Login log: Query system login log records, including login exceptions.
11. Online users: Monitor the status of currently active users in the system.
12. Scheduled tasks: Online (add, modify, delete) task scheduling, including execution-result logs.
13. Service monitoring: Monitor the current system's CPU, memory, disk, stack, and other related information.
14. Cache monitoring: Query the system's cache information, command statistics, etc.
15. System interface: Automatically generate the relevant api interface documentation based on the business code.
