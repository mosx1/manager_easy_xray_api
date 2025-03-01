Апи для управления проектом https://github.com/EvgenyNerush/easy-xray.git
Проект необходимо запускать без докера, как и это апи.
Для работы используется драйвер для подключения к PostgreSQL. В целях безопасности реализовано хранение закрытого ключа в таблице БД.
Схема таблицы:
NAME TABLE securityhashs
COLUMN hash (text)
COLUMN data (timestamp)

Рекомендую обновлять токен раз в час.