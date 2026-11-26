# Дорожная карта Rust-NTM

## Цель и эталоны

Rust-NTM реализует собственные сервер, клиент и API расширений для игровых сценариев Minecraft Java Edition 1.7.10. Архитектурные решения других Rust-проектов можно сравнивать по конкретным подсистемам. При включении стороннего компонента фиксируются его назначение, версия и лицензия.

Спецификации и отчёты S01–S11 описывают измерения на Java/Forge, команды воспроизведения и оставшиеся пробелы. Эталон определяет ожидаемое поведение на конкретном входе. Приёмка Rust требует отдельного прогона на том же входе. Результаты собираются по сценарию, версии, seed, условиям запуска и фактическому выводу. Допуски определяются до сравнения.

## Первый сеанс

1. Собрать сервер, проверить эталоны и настроить CI ([D01](https://github.com/zenoaugmentis/Rust-NTM/issues/132), [D02](https://github.com/zenoaugmentis/Rust-NTM/issues/133), [D03](https://github.com/zenoaugmentis/Rust-NTM/issues/134)).
2. Параллельно реализовать status и login по протоколу 5, чтение плоского мира и фоновую загрузку ([D04](https://github.com/zenoaugmentis/Rust-NTM/issues/135)–[D07](https://github.com/zenoaugmentis/Rust-NTM/issues/138)).
3. Отправить готовую область spawn, принять движение ванильного клиента, задержать соседний чанк в тесте, проверить позицию и урон ([D08](https://github.com/zenoaugmentis/Rust-NTM/issues/139), [D09](https://github.com/zenoaugmentis/Rust-NTM/issues/140)).
4. Изменить блок, сохранить мир и позицию, перезапустить сервер и повторно войти. Измерить задержки тика и загрузки при одинаковой работе ([D10](https://github.com/zenoaugmentis/Rust-NTM/issues/141), [D11](https://github.com/zenoaugmentis/Rust-NTM/issues/142)).

Сервер владеет состоянием мира. Фоновые задачи готовят данные, игровой тик принимает готовые результаты в воспроизводимом порядке. Физика различает отсутствующий чанк и загруженный воздух. Проверка первого сеанса использует ванильный клиент; собственный клиент проходит свою проверку в M13.

## Этапы и приёмка

| Этап | Результат | Задачи |
|---|---|---|
| [M10](https://github.com/zenoaugmentis/Rust-NTM/issues/126) · Основа Rust-NTM | Из чистого checkout собирается сервер и выполняются проверки существующих эталонов. | [D01](https://github.com/zenoaugmentis/Rust-NTM/issues/132), [D02](https://github.com/zenoaugmentis/Rust-NTM/issues/133), [D03](https://github.com/zenoaugmentis/Rust-NTM/issues/134) |
| [M11](https://github.com/zenoaugmentis/Rust-NTM/issues/127) · Первый игровой сеанс | Ванильный клиент 1.7.10 входит на Rust-сервер, двигается по плоскому миру и возвращается к сохранённому состоянию. | [D04](https://github.com/zenoaugmentis/Rust-NTM/issues/135), [D05](https://github.com/zenoaugmentis/Rust-NTM/issues/136), [D06](https://github.com/zenoaugmentis/Rust-NTM/issues/137), [D07](https://github.com/zenoaugmentis/Rust-NTM/issues/138), [D08](https://github.com/zenoaugmentis/Rust-NTM/issues/139), [D09](https://github.com/zenoaugmentis/Rust-NTM/issues/140), [D10](https://github.com/zenoaugmentis/Rust-NTM/issues/141), [D11](https://github.com/zenoaugmentis/Rust-NTM/issues/142) |
| [M12](https://github.com/zenoaugmentis/Rust-NTM/issues/128) · Ванильная симуляция и мир | Генерация, сущности, механики и сетевое состояние сравниваются с наблюдаемым поведением 1.7.10. | [D12](https://github.com/zenoaugmentis/Rust-NTM/issues/143), [D13](https://github.com/zenoaugmentis/Rust-NTM/issues/144), [D14](https://github.com/zenoaugmentis/Rust-NTM/issues/145), [D15](https://github.com/zenoaugmentis/Rust-NTM/issues/146), [D16](https://github.com/zenoaugmentis/Rust-NTM/issues/147), [D17](https://github.com/zenoaugmentis/Rust-NTM/issues/148), [D18](https://github.com/zenoaugmentis/Rust-NTM/issues/149) |
| [M13](https://github.com/zenoaugmentis/Rust-NTM/issues/129) · Собственный клиент | Rust-клиент открывает мир по протоколу 5, отображает ресурсы 1.7.10 и проходит игровой сценарий. | [D19](https://github.com/zenoaugmentis/Rust-NTM/issues/150), [D20](https://github.com/zenoaugmentis/Rust-NTM/issues/151), [D21](https://github.com/zenoaugmentis/Rust-NTM/issues/152), [D22](https://github.com/zenoaugmentis/Rust-NTM/issues/153) |
| [M14](https://github.com/zenoaugmentis/Rust-NTM/issues/130) · Расширения движка | Тестовый мод регистрирует контент, сохраняет состояние и синхронизирует его между клиентами. | [D23](https://github.com/zenoaugmentis/Rust-NTM/issues/154), [D24](https://github.com/zenoaugmentis/Rust-NTM/issues/155), [D25](https://github.com/zenoaugmentis/Rust-NTM/issues/156), [D26](https://github.com/zenoaugmentis/Rust-NTM/issues/157), [D27](https://github.com/zenoaugmentis/Rust-NTM/issues/158) |
| [M15](https://github.com/zenoaugmentis/Rust-NTM/issues/131) · Модовые прототипы | Для HBM’s NTM, MCHeli и OpenComputers воспроизводится по одному сквозному сценарию на нативной реализации. | [D28](https://github.com/zenoaugmentis/Rust-NTM/issues/159), [D29](https://github.com/zenoaugmentis/Rust-NTM/issues/160), [D30](https://github.com/zenoaugmentis/Rust-NTM/issues/161), [D31](https://github.com/zenoaugmentis/Rust-NTM/issues/162) |

Модовые прототипы используют наблюдаемое поведение выбранных билдов Forge. Для каждого согласуются объём, параметры опыта и происхождение ресурсов. Регистрация, сохранение, установка и каналы синхронизации проверяются на собственном API. Совместимость с оригинальными Java-модами на уровне исполнения JAR в этот план не входит.

## Сохранённые материалы

| Проверка | Источники |
|---|---|
| Версии, мир, блоки и расширенные ID | [S01](specs/versions.md), [S02](contracts/blocks.md), [S03](specs/chunks-1.7.10.md), [S06](reports/S06-reproduce.md) |
| Сеть и вход | [S04](specs/protocol-5.md), [шифрование и границы проверки](specs/protocol-5-encryption.md), [S07](reports/S07-manual-2026-11-18.md) |
| Ресурсы, инвентарь и симуляция | [S05](specs/assets-1.7.10.md), [S08](reports/S08-manual-2026-11-20.md), [S09](specs/gameplay-1.7.10.md) |
| Моды, прогоны и неизвестные | [S10](specs/mod-api.md), [матрица и реестр S11](PARITY_MATRIX.md), [отчёты и свидетельства](reports/) |

В S10 описаны как наблюдения Forge, так и прежнее предложение формата модов Horizon. В S11 сохранена историческая матрица M0–M9 с исходными результатами. Текущие критерии приёмки перечислены в [бэклоге](../planning/backlog.json) и новых issues. Старый план и его CSV доступны на [ревизии до переустройства](https://github.com/zenoaugmentis/Rust-NTM/tree/d833b92b8e8cbb48f2b229dd0b3d210a3527a0ea/planning).
