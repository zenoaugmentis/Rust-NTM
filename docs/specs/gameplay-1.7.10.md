# S09 · Эталон игрового поведения Minecraft 1.7.10

Ручной прогон Zeno от 2026-11-20. Задача [#22](https://github.com/zenoaugmentis/horizon-NTM/issues/22).

## Стенд

Ванильные клиент и dedicated server 1.7.10, Windows, локальное подключение. Перед запуском SHA-1 обоих JAR совпали с эталоном [S01](versions.md).

| Компонент | SHA-1 |
| --- | --- |
| Клиент | `e80d9b3bf5085002218d4be59e668bac718abbc6` |
| Сервер | `952438ac4e01b4d115c5fc38f891710c4941df29` |

Для повторения скопировать серверный JAR, конфиг Log4j и ранее принятый `eula.txt` из стенда S01 в отдельный каталог вне репозитория. Создать в нём `server.properties`.

```properties
server-ip=127.0.0.1
server-port=25569
online-mode=false
level-name=s09-flat
level-type=FLAT
level-seed=909
generate-structures=false
spawn-animals=false
spawn-monsters=false
spawn-npcs=false
gamemode=0
difficulty=1
enable-command-block=true
view-distance=3
motd=Horizon S09 vanilla reference
```

Запуск из каталога стенда в PowerShell. Команда использует путь к Java из S01. При другой установке подставить свой путь к `java.exe`.

```powershell
$java = Join-Path $env:APPDATA '.tlauncher\legacy\Minecraft\jre\jre-legacy\windows-x64\jre-legacy\bin\java.exe'; & $java '-Dlog4j.configurationFile=log4j2_17-111.xml' -Xms256M -Xmx768M -jar '.\minecraft_server.1.7.10.jar' nogui
```

Сервер подготовил `s09-flat` и сообщил `Done (0.766s)!`. Ванильный клиент подключился к `127.0.0.1:25569`. Ниже `PLAYER` обозначает имя подключённого игрока. Все игровые команды вводятся в консоль сервера по одной строке, без начального `/`. Опыты рассчитаны на свежую площадку без посторонних блоков и источников питания.

## Наблюдения

| Область | Опыт | Результат |
| --- | --- | --- |
| Движение | Пройти в полный каменный блок без прыжка | Остановка на `(466.70000, 4.000, -550.49985)` |
| Движение | Запрыгнуть на блок | Приземление на `(467.34922, 5.000, -550.42011)` |
| Урон | Снять опору под игроком на высоте 3 / 4 / 8 блоков над землёй | Урон 0 / 1 / 5 HP соответственно, по индикатору сердец |
| Серверные тики | `debug start` / `debug stop`, один игрок стоит на месте | 557 тиков за 27.852 с, примерно 20 тиков/с |
| Обновление блоков | Установить песок и камень в воздухе на `Y=9` | Песок оказался на `Y=4`, камень остался на `Y=9`. Четыре итоговые проверки прошли |
| Redstone | Прямая ветка и ветка с двумя повторителями, общий источник | Обе лампы погашены до опыта, горят после подачи питания и гаснут после снятия. Оба повторителя меняют состояние. Десять проверок прошли |

### Движение и столкновение

```text
gamemode 0 PLAYER
setblock 467 4 -551 minecraft:stone
tp PLAYER 465.5 4 -550.5
```

Включить F3, повернуться к блоку и идти прямо в него. Записать координаты после упора, используя `feet pos` для Y. Затем прыгнуть вперёд и отпустить W над блоком. Записать координаты после устойчивого приземления. Положение на блоке зависит от ручного ввода, поэтому критерием воспроизведения служат остановка перед гранью блока и подъём с `Y=4` на `Y=5`.

### Урон от падения

```text
gamerule naturalRegeneration false
```

Использовать Survival без брони. Перед каждым прогоном подтвердить полное здоровье по HUD. При необходимости между прогонами выполнить `effect PLAYER 6 1 4` и дождаться полного здоровья. Сначала поставить опору, затем телепортироваться на неё, сверить высоту ног и убрать опору, стоя на месте. Приземление рассчитано на поверхность с высотой ног `Y=4`.

| Номинальная высота | Поставить опору | Встать на опору | Убрать опору | HUD до → после |
| --- | --- | --- | --- | --- |
| 3 | `setblock 465 6 -551 minecraft:stone` | `tp PLAYER 465.5 7 -550.5` | `setblock 465 6 -551 minecraft:air` | 10 → 10 сердец (20 → 20 HP) |
| 4 | `setblock 465 7 -551 minecraft:stone` | `tp PLAYER 465.5 8 -550.5` | `setblock 465 7 -551 minecraft:air` | 10 → 9.5 сердец (20 → 19 HP) |
| 8 | `setblock 465 11 -551 minecraft:stone` | `tp PLAYER 465.5 12 -550.5` | `setblock 465 11 -551 minecraft:air` | 10 → 7.5 сердец (20 → 15 HP) |

Высоты в таблице заданы геометрией опыта. Для каждого падения присланы показания здоровья, отдельные записи F3 до и после отсутствуют.

### Серверные тики и обновление песка

Ввести `debug start`, подождать несколько десятков секунд и ввести `debug stop`. В ручном прогоне команда показала 27.852 с и 557 тиков. Отношение `557 / 27.852` даёт около 19.999 TPS за всё окно профилирования.

Для проверки обновления блоков выполнить подготовительные команды.

```text
testforblock 469 4 -551 minecraft:air
testforblock 470 4 -551 minecraft:air
setblock 469 9 -551 minecraft:sand
setblock 470 9 -551 minecraft:stone
```

Подождать пару секунд и выполнить итоговые проверки. В ручном прогоне все четыре команды вернули `Successfully found the block` на указанных координатах.

```text
testforblock 469 9 -551 minecraft:air
testforblock 469 4 -551 minecraft:sand
testforblock 470 9 -551 minecraft:stone
testforblock 470 4 -551 minecraft:air
```

### Redstone

Собрать две ветки с общим источником в `(465, 4, -547)`. Прямая лампа стоит сбоку от источника, вторая получает питание через повторители вдоль +X. В legacy metadata значение `13` задаёт направление на восток и 4 redstone-тика задержки на повторитель. [Таблица legacy metadata](https://minecraft.fandom.com/wiki/Java_Edition_data_values/Pre-flattening#Redstone_Repeater)

**Сборка и исходное состояние.** Обе проверки прошли.

```text
setblock 465 4 -548 minecraft:redstone_lamp
setblock 466 4 -547 minecraft:unpowered_repeater 13
setblock 467 4 -547 minecraft:unpowered_repeater 13
setblock 468 4 -547 minecraft:redstone_lamp
testforblock 465 4 -548 minecraft:redstone_lamp
testforblock 468 4 -547 minecraft:redstone_lamp
```

**Подача питания.** Поставить источник, подождать пару секунд, затем выполнить проверки. Все четыре прошли.

```text
setblock 465 4 -547 minecraft:redstone_block
testforblock 465 4 -548 minecraft:lit_redstone_lamp
testforblock 466 4 -547 minecraft:powered_repeater 13
testforblock 467 4 -547 minecraft:powered_repeater 13
testforblock 468 4 -547 minecraft:lit_redstone_lamp
```

**Снятие питания.** Убрать источник, подождать пару секунд, затем выполнить проверки. Все четыре прошли.

```text
setblock 465 4 -547 minecraft:air
testforblock 465 4 -548 minecraft:redstone_lamp
testforblock 466 4 -547 minecraft:unpowered_repeater 13
testforblock 467 4 -547 minecraft:unpowered_repeater 13
testforblock 468 4 -547 minecraft:redstone_lamp
```

Расчётная задержка включения в ветке с повторителями — 8 redstone-тиков, то есть 16 игровых тиков. Команды проверяют устойчивые состояния. Фактический интервал и порядок отдельных переключений не измерялись. [Задержка повторителя](https://minecraft.wiki/w/Redstone_component#Redstone_repeater)

## Границы эталона

В отчёте зафиксированы результаты конкретных сценариев ванили 1.7.10. Траектория прыжка по тикам, урон за пределами проверенных высот, random ticks и точные задержки обновлений остаются открытыми. Сравнительного прогона на Horizon 26.3 и проверки исходного upstream SHA в S09 не было. Материал предназначен для последующих задач по переносу механик и проверки совместимости.
