---
title: "Обзор"
description: "Краткий обзор ComfyUI Arena Suite и навигация по документации."
---

Обзор · [Быстрый старт](quickstart.md) · [Arena AutoCache Base](arena_autocache_base.md) · [Узлы](nodes.md) · [Диагностика](troubleshooting.md)

---

# 🅰️ ComfyUI Arena Suite

> TL;DR — Arena AutoCache (simple) v4.2.4
> - Production-готовая нода для кеширования моделей
> - OnDemand режим - прозрачное кеширование при первом обращении
> - Полная настройка через .env файлы с автопатчем
> - Потокобезопасная дедупликация и безопасная очистка кэша
> - LRU-pruning до 95% лимита с подробным логированием
> - Усиленная безопасность очистки с проверкой глубины путей
> - Deferred autopatch - отложенный автопатч для лучшей совместимости

Arena Suite объединяет: production-готовую ноду Arena AutoCache (simple) и legacy узлы.

## Возможности
- **🅰️ Arena AutoCache (simple) v4.2.4** — production-готовая нода для кеширования моделей
- **Legacy узлы** — Arena Make Tiles Segments и другие
- **Production-ready архитектура** — thread-safe, безопасная очистка, LRU-pruning
- **Усиленная безопасность** — строгие проверки глубины путей для всех платформ

## Требования
- ComfyUI (актуальный master)
- Python 3.10+
- SSD для лучшей производительности AutoCache

---

[Далее: Быстрый старт →](quickstart.md)

