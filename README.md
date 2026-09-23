API для управления проектом https://github.com/EvgenyNerush/easy-xray.git
Проект запускается в Docker или без него. Для работы используется PostgreSQL
(asyncpg). Таблицы создаются через `GET /initdb/` (SQLModel metadata).

## Схема БД

### securityhashs

Токен API для проверки `successAuth`. Рекомендуется обновлять раз в час.

| Поле   | Тип                     | Описание        |
|--------|-------------------------|-----------------|
| hash   | text, PK                | Токен запросов  |
| data   | timestamp without time zone | Время записи |

### servers

Узлы Xray. Запись ищется по `links` (подстрока `hostName` из `config.ini`).

| Поле  | Тип        | Описание                          |
|-------|------------|-----------------------------------|
| id    | bigint, PK | Идентификатор сервера             |
| links | text       | Домен/ссылка (например, hostname) |

### configs_servers

Актуальный JSON-конфиг Xray для сервера (хранится в PostgreSQL JSONB).

| Поле      | Тип        | Описание                    |
|-----------|------------|-----------------------------|
| id        | bigint, PK | Идентификатор записи        |
| server_id | bigint, FK | `servers.id`                |
| config    | jsonb      | Конфигурация Xray (сервер)  |

### users

Пользователи VPN (Telegram и привязка к серверу).

| Поле           | Тип                     | Описание                          |
|----------------|-------------------------|-----------------------------------|
| telegram_id    | bigint, PK              | Telegram ID                       |
| name           | text, nullable          | Имя                               |
| exit_date      | timestamp without time zone | Дата окончания доступа        |
| action         | boolean                 | Активность                        |
| server_link    | text                    | Ссылка на конфиг                  |
| server_id      | bigint, FK              | `servers.id`                      |
| server_desired | char, nullable          | Желаемый сервер                   |
| paid           | boolean                 | Оплачен                           |
| protocol       | bigint                  | Протокол                          |
| statistic      | text, nullable          | Статистика                        |
| balance        | numeric, nullable       | Баланс                            |
| invited        | bigint, FK, nullable    | `users.telegram_id` (реферал)   |

Связи:

- `configs_servers.server_id` → `servers.id`
- `users.server_id` → `servers.id`
- `users.invited` → `users.telegram_id`

Перед первым `/add` на новом хосте нужны строка в `servers` (с `links`, содержащим
`Xray.hostName`) и конфиг в `configs_servers` (создаётся через `/install_xray`).

Для конфигурации приложения создайте файл config.ini. В Docker он монтируется в контейнер
read-only и не попадает в образ.
```
[Paths]
jsonConfig = ./easy-xray-main/conf/

[DataBase]
dialect = Unknown
driver = Unknown
username = Unknown
password = Unknown
host = Unknown
database = Unknown

[Xray]
hostName = Unknown
port = 443
public_key = Unknown
private_key = Unknown
fake_site = duckduckgo.com
```

## Docker

Сборка и локальный запуск:

```bash
docker build -t manager-easy-xray-api:latest .
docker run --name manager-easy-xray-api \
  --restart unless-stopped \
  -p 443:443/tcp \
  -p 8081:8081/tcp \
  -v "$(pwd)/config.ini:/fastapiapp/config.ini:ro" \
  manager-easy-xray-api:latest
```

После запуска API восстанавливает конфигурацию Xray из PostgreSQL, если она
уже есть, и запускает Xray. Состояние контейнера доступно по адресу
`GET /health`. Первый запуск на новом сервере требует `GET /install_xray`.

## GitHub CI/CD

Workflow `.github/workflows/deploy.yml` собирает multi-architecture образ,
публикует его в GHCR (`ghcr.io/<owner>/<repo>:sha-<commit>` и `:latest`) и
разворачивает на выбранный GitHub Environment по SSH. Деплой запускается
вручную: **Actions → Build and deploy → Run workflow**, затем выбирается
Environment, например `fn2`.

### Подготовка сервера

На сервере должны быть установлены Docker и пользователь для деплоя, имеющий
доступ к Docker daemon. Для `fn2.kuzmos.ru`:

```bash
sudo mkdir -p /opt/manager-easy-xray-api
sudo cp config.ini /opt/manager-easy-xray-api/config.ini
sudo chmod 600 /opt/manager-easy-xray-api/config.ini
sudo chown -R <ssh-user>:<ssh-user> /opt/manager-easy-xray-api
```

Порты `443/tcp` и `8081/tcp` должны быть свободны и разрешены в firewall.
Пакет GHCR должен быть доступен серверу: workflow логинится в `ghcr.io` на
время деплоя через `GITHUB_TOKEN`.

### Настройка GitHub Environment

В репозитории откройте **Settings → Environments** и создайте Environment
`fn2`. Добавьте в него secrets:

- `SSH_HOST` — `fn2.kuzmos.ru`;
- `SSH_USER` — пользователь сервера с доступом к Docker;
- `SSH_PRIVATE_KEY` — приватный SSH-ключ без passphrase;
- `SSH_KNOWN_HOSTS` — доверенная строка host key сервера;
- `SSH_PORT` — SSH-порт, необязательно; по умолчанию `22`.

Значение `SSH_KNOWN_HOSTS` можно получить с доверенной машины:

```bash
ssh-keyscan -H fn2.kuzmos.ru
```

Перед добавлением сверяйте fingerprint ключа с ключом сервера. Для следующего
сервера создайте отдельный GitHub Environment с теми же именами secrets.

При неуспешном healthcheck workflow выводит логи нового контейнера и запускает
предыдущий образ.
