# S10 · Контракт Mod API и совместимость с Forge 1.7.10

Задача [#23](https://github.com/zenoaugmentis/Rust-NTM/issues/23). Ручной прогон выполнил Zeno 21 ноября 2026 года на Windows.
Контрольный коммит проекта — `04bb83b739b4ebb7695bbec266138379e73e422f`. Зависимости — [S02](blocks.md) и [S08](https://github.com/zenoaugmentis/Rust-NTM/pull/121).

Стенд — клиент Minecraft 1.7.10, Forge 10.13.4.1614, FML 7.99.40.1614 и `OpenComputers-MC1.7.10-1.8.10+667626d-universal.jar`. Игровой каталог — `%USERPROFILE%\Documents\horizon-reference`. Для чтения NBT использовался `nbtlib`. Команды ниже приведены из прогона. Из вывода оставлены строки, по которым проверялся результат.

## Native-порт и Forge JAR

**Что установили.** Java-версия OpenComputers загрузилась как мод Forge в Minecraft 1.7.10. Она служит эталоном для сравнения регистрации, сохранения и поведения при подключении. По документации Horizon на ревизии `447e9d277d06272196ba66363d5ea8d582581c63` нативный мод поставляется как `.hnmod` и собирается для подходящей ревизии Horizon. Декларативный пакет `.hmod` содержит данные и ресурсы. [Форматы модов Horizon](https://github.com/horizon-rust/horizon/blob/447e9d277d06272196ba66363d5ea8d582581c63/docs/mods.md) · [Сборка нативных модов](https://github.com/horizon-rust/horizon/blob/447e9d277d06272196ba66363d5ea8d582581c63/docs/native-mods.md)

**Как проверили.** Сверили бинарники эталонного клиента и Forge с [S01](../specs/versions.md), затем запустили Forge-профиль. Хеш JAR OpenComputers записали для повторения опыта. Проверка запуска описана в следующем разделе.

```powershell
$ref = Join-Path $env:USERPROFILE 'Documents\horizon-reference'; $jars = [ordered]@{ CLIENT = 'versions\1.7.10\1.7.10.jar'; FORGE = 'libraries\net\minecraftforge\forge\1.7.10-10.13.4.1614-1.7.10\forge-1.7.10-10.13.4.1614-1.7.10.jar' }; foreach ($key in $jars.Keys) { $path = Join-Path $ref $jars[$key]; if (Test-Path -LiteralPath $path -PathType Leaf) { "${key}_SHA1=$((Get-FileHash -LiteralPath $path -Algorithm SHA1).Hash)" } else { "${key}_SHA1=MISSING" } }; $mods = @(Get-ChildItem -LiteralPath (Join-Path $ref 'mods') -Filter '*OpenComputers*.jar' -File -ErrorAction SilentlyContinue); if ($mods.Count -eq 0) { 'OPENCOMPUTERS=MISSING_IN_MODS' }; $mods | ForEach-Object { "OPENCOMPUTERS=$($_.Name) SHA256=$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
```

```text
CLIENT_SHA1=E80D9B3BF5085002218D4BE59E668BAC718ABBC6
FORGE_SHA1=25FD97F72BECA728112256938E03E8105B1B78CC
```

Первый поиск мода вернул `OPENCOMPUTERS=MISSING_IN_MODS`. Повторный поиск нашёл JAR в `horizon-reference\mods`:

```powershell
$ref = Join-Path $env:USERPROFILE 'Documents\horizon-reference'; $roots = @($ref, (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:APPDATA '.minecraft\mods'), (Join-Path $env:APPDATA '.tlauncher\legacy\Minecraft\mods')); $hits = @($roots | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | ForEach-Object { Get-ChildItem -LiteralPath $_ -Recurse -File -Filter '*OpenComputers*.jar*' -ErrorAction SilentlyContinue } | Sort-Object FullName -Unique); if ($hits.Count -eq 0) { 'OC_JAR=NOT_FOUND' } else { $hits | ForEach-Object { "OC_JAR=$($_.FullName) SHA256=$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" } }
```

```text
OC_JAR=<игровой каталог>\mods\OpenComputers-MC1.7.10-1.8.10+667626d-universal.jar SHA256=40DBD0857EFE6EFF0C8B40965A7B98B689BF0B328194DFA1AC458088073376E9
```

**Контракт Horizon-NTM.**

- Поведение Java-мода переносится в нативный код с явно указанной совместимостью движка и API. Сборка нативного кода требует доверия к моду.
- Если пользователь передаёт Forge JAR загрузчику Horizon-NTM, тот должен сообщить о неподдерживаемом формате. Поддержка JVM, Forge Java API, трансформеров и coremods не входит в S10.
- Импорт сохранений оценивается отдельно от порта поведения. Для конкретного порта указываются поддерживаемые типы, состояние и сетевые функции.
- Проверка для будущего загрузчика: совместимый нативный пакет проходит проверку манифеста, Forge JAR получает диагностику формата. Такой запуск на Horizon ещё не выполнялся. Указанная ревизия Horizon использовалась для сверки документации. Закрепление базы проекта относится к [A02](https://github.com/zenoaugmentis/Rust-NTM/issues/6).

## Lifecycle

**Что обнаружили.** FML обнаружил пять модов, завершил загрузку и открыл мир на встроенном сервере. При выходе сохранил Overworld, Nether и The End. Фазы pre-init, init и post-init сверены по исходнику загрузчика FML. Журнал этого опыта показывает завершение загрузки и события мира. Вызовы отдельных обработчиков не трассировались. [FML Loader](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/Loader.java)

**Как проверили.** В Forge-профиле с OpenComputers создали суперплоский творческий мир `S10-forge-api`. После загрузки нажали «Сохранить и выйти». Отфильтровали журнал PowerShell-командой:

```powershell
$ref = Join-Path $env:USERPROFILE 'Documents\horizon-reference'; $logs = @(Get-ChildItem -LiteralPath (Join-Path $ref 'logs') -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -in @('fml-client-latest.log', 'latest.log') }); if ($logs.Count -eq 0) { 'S10_LOG=MISSING' }; foreach ($log in $logs) { "LOG=$($log.Name) UPDATED=$($log.LastWriteTime.ToString('s'))"; Select-String -LiteralPath $log.FullName -Pattern 'Forge Mod Loader version', 'MinecraftForge v', 'identified .* mods', 'successfully loaded .* mods', 'OpenComputers.*1\.8\.10', 'S10-forge-api' | Select-Object -Last 20 | ForEach-Object { $_.Line } }
```

**Ожидали** успешную загрузку Forge, открытие мира и сохранение чанков при выходе. **Получили** следующие строки:

```text
Forge Mod Loader version 7.99.40.1614 for Minecraft 1.7.10 loading
MinecraftForge v10.13.4.1614 Initialized
Forge Mod Loader has identified 5 mods to load
Forge Mod Loader has successfully loaded 5 mods
Loading dimension 0 (S10-forge-api)
Saving chunks for level 'S10-forge-api'/Overworld
Saving chunks for level 'S10-forge-api'/Nether
Saving chunks for level 'S10-forge-api'/The End
```

**Контракт Horizon-NTM.** Прочитать манифесты с ID, версией, версией API, зависимостями и сторонами исполнения. Проверить весь набор и определить детерминированный порядок с зависимостями перед потребителями. Зарегистрировать типы, обработчики и сообщения, разрешить взаимные ссылки и зафиксировать схему. Затем открыть мир и привязать его карту ID. При закрытии штатно завершить сохранение и освободить контекст мира. Следующее открытие заново привязывает карту. Приёмочные случаи для реализации: зависимость A загружается перед B, который её требует; отсутствие A, цикл зависимостей и дублирующийся ID диагностируются до открытия мира.

## Register

**Что обнаружили.** Новый мир содержит 80 записей OpenComputers. Префикс `1` в `FML.ItemData` обозначает блок, `2` — предмет. У `accessPoint` и `assembler` имя и ID совпадают у блока и его `ItemBlock`. `OpenComputers:item` зарегистрирован как предмет с ID `4096`. Числа относятся к этому миру. [FML GameData](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/registry/GameData.java) · [S02](blocks.md)

**Как проверили.** После выхода из мира прочитали `level.dat` командой:

```powershell
$save = Join-Path $env:USERPROFILE 'Documents\horizon-reference\saves\S10-forge-api\level.dat'; if (Test-Path -LiteralPath $save -PathType Leaf) { py -c "import sys, nbtlib; f = nbtlib.load(sys.argv[1])['FML']; rows = sorted((ord(str(e['K'])[0]), str(e['K'])[1:], int(e['V'])) for e in f['ItemData'] if str(e['K'])[1:].lower().startswith('opencomputers:')); print('OC_REGISTRY_COUNT=' + str(len(rows))); print('OC_BLOCKS=' + str(sum(k == 1 for k, _, _ in rows))); print('OC_ITEMS=' + str(sum(k == 2 for k, _, _ in rows))); print('OC_EXAMPLES=' + repr([r for r in rows if r[1].lower() in ('opencomputers:assembler', 'opencomputers:accesspoint', 'opencomputers:item')])); print('OC_MODLIST=' + repr([m.snbt() for m in f.get('ModList', []) if 'opencomputers' in str(m.get('ModId', '')).lower()]))" "$save" } else { 'S10_LEVEL_DAT=MISSING' }
```

**Ожидали** записи блока и предмета и привязки в карте нового мира, сопоставимые с S08. **Получили:**

```text
OC_REGISTRY_COUNT=80
OC_BLOCKS=38
OC_ITEMS=42
OC_EXAMPLES=[(1, 'OpenComputers:accessPoint', 165), (1, 'OpenComputers:assembler', 167), (2, 'OpenComputers:accessPoint', 165), (2, 'OpenComputers:assembler', 167), (2, 'OpenComputers:item', 4096)]
OC_MODLIST=['{ModVersion: "1.8.10", ModId: "OpenComputers|Core"}', '{ModVersion: "1.8.10", ModId: "OpenComputers"}']
```

Отдельно запустили тесты модели реестра S02 из корня репозитория. Ожидали код выхода `0`. Проверки охватывают конфликты, фиксацию реестра, приоритет карты мира, сохранение ID пропавшего мода и применение карты сервера на клиенте.

```powershell
python -B -m unittest discover -s tests -p 'test_legacy_blocks.py' -v; "S02_EXIT=$LASTEXITCODE"
```

```text
Ran 23 tests in 0.980s
OK
S02_EXIT=0
```

**Контракт Horizon-NTM.** Ключ регистрации — тип реестра и имя с пространством имён. Повтор ключа в одном реестре — ошибка. Блок и его `ItemBlock` используют один legacy ID, сохраняя отдельные записи. Схема фиксируется до открытия мира. Числовые привязки S02 берутся из карты мира, а в сетевой сессии клиент применяет карту сервера. Приёмочные случаи: одно имя для блока и `ItemBlock` с одним ID разрешено; повторная регистрация блока под тем же ключом отклоняется; при открытии существующего мира сохранённый ID имеет приоритет над новым назначением.

## Tick

**Что обнаружили.** На запущенном компьютере OpenComputers Lua продолжил выполнение после трёхсекундного ожидания. `computer.uptime()` вырос ровно на `3.0`. Это наблюдение о работе мода. По нему нельзя определить число тиков мира, сторону вызова каждой функции или порядок обработчиков Forge. Фазы и стороны сверены по исходнику `TickEvent`. [FML TickEvent](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/gameevent/TickEvent.java)

**Как проверили.** В мире `S10-forge-api` использовали `Computer Case (Creative)` и OpenOS на HDD. Открыли `lua` и выполнили:

```lua
local c = require("computer"); local t = c.uptime(); print("S10_TICK_BEGIN", t); os.sleep(3); print("S10_TICK_END", c.uptime(), "DELTA", c.uptime() - t)
```

**Ожидали** вторую строку после ожидания и положительную разницу времени. **Получили:**

```text
S10_TICK_BEGIN  18.2
S10_TICK_END    21.2    DELTA   3.0
```

**Контракт Horizon-NTM.** Мир меняет логический сервер, включая встроенный сервер. API различает начало и конец тика и предоставляет контекст мира там, где событие к нему относится. Внутри фазы порядок обработчиков определяется зависимостями и порядком регистрации. Блочные сущности обновляются в чанках, активных для симуляции. Случайные и запланированные обновления блоков имеют отдельные механизмы. Приёмочный случай для Rust: тестовая блочная сущность увеличивает счётчик один раз за серверный тик, а клиентская фаза и неактивный чанк счётчик не меняют. Для проверки порядка фаз нужен собственный тест с наблюдаемыми обработчиками.

## Save

**Что обнаружили.** Файл на HDD OpenComputers сохранился после закрытия и повторного открытия мира. Этот опыт проверяет данные диска. Сохранение активного Lua-процесса, конкретные поля NBT блочной сущности и аварийное восстановление здесь не проверялись. Структура реестра Forge сверена отдельно в `level.dat`. [FMLContainer](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/FMLContainer.java)

**Как проверили.** В той же Lua-сессии записали контрольное значение:

```lua
local f = assert(io.open("/s10-state.txt", "w")); assert(f:write("S10_STATE=17\n")); f:close(); print("S10_WRITE_DONE")
```

Вышли из Lua и выполнили `cat /s10-state.txt` в OpenOS. Затем сохранили и закрыли мир, снова открыли его и повторили ту же команду на том же компьютере.

**Ожидали** успешную запись и одинаковое значение до и после открытия. **Получили:**

```text
S10_WRITE_DONE

Перед закрытием мира
/home # cat /s10-state.txt
S10_STATE=17

После повторного открытия мира
/home # cat /s10-state.txt
S10_STATE=17
```

**Контракт Horizon-NTM.** На загрузке сначала восстановить карту ID по S02 и затем декодировать чанки и ItemStack по ней. Нативное состояние содержит тип объекта, версию схемы и данные. Для неизвестного типа сохранить исходную запись и сообщить о проблеме. При миграции проверить результат перед сохранением. Для W11 приёмочный случай — сохранить блочную сущность с известным состоянием, закрыть мир, открыть его и прочитать то же состояние до следующего тика. Для порта OpenComputers содержимое диска и активное состояние машины проверяются отдельными сценариями.

## Packets

**Что обнаружили.** Dedicated Forge-сервер пустил клиент с OpenComputers 1.8.10 и отклонил тот же профиль без мода. Число `2` в `Client protocol version 2` относится к рукопожатию FML. Номер основного протокола Minecraft 1.7.10 — `5` по S04. Передача карты ID следует из исходников клиентского и серверного автоматов FML. Байты кадров, карта ID на проводе и прикладные пакеты OpenComputers не захватывались. [Серверный автомат FML](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/network/handshake/FMLHandshakeServerState.java) · [Клиентский автомат FML](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/network/handshake/FMLHandshakeClientState.java)

**Как проверили.** В отдельный каталог сервера установили Forge через `--installServer` и положили тот же JAR OpenComputers в серверный `mods`. Сервер работал на `127.0.0.1:25570` с `online-mode=false` и миром `S10-forge-network`. Запускали его на Java 8 с конфигом Log4j из S01, где `$java` — путь к Java, а `$forge` — объект файла серверного Forge JAR:

```powershell
& $java '-Dlog4j.configurationFile=log4j2_17-111.xml' -Xms256M -Xmx1G -jar $forge.FullName nogui
```

Подключились через меню мультиплеера. **Ожидали** успешный вход с установленным модом. **Получили** загрузку мира и такие строки:

```text
Done (1.007s)! For help, type "help" or "?"
Client protocol version 2
Client attempting to join with 5 mods : FML@7.10.99.99,OpenComputers|Core@1.8.10,OpenComputers@1.8.10,Forge@10.13.4.1614,mcp@9.05
Attempting connection with missing mods [] at CLIENT
[Server thread] Server side modded connection established
```

Закрыли клиент, оставили сервер запущенным и временно вынесли JAR из клиентского `mods`:

```powershell
$ref = Join-Path $env:USERPROFILE 'Documents\horizon-reference'; $oc = 'OpenComputers-MC1.7.10-1.8.10+667626d-universal.jar'; $clientJar = Join-Path $ref "mods\$oc"; $hold = Join-Path $ref "S10-disabled-$oc"; if (Test-Path -LiteralPath $hold) { throw "BACKUP_ALREADY_EXISTS=$hold" }; Move-Item -LiteralPath $clientJar -Destination $hold -ErrorAction Stop; "CLIENT_OC_PRESENT=$(Test-Path -LiteralPath $clientJar)"
```

```text
CLIENT_OC_PRESENT=False
```

После перезапуска того же Forge-профиля повторили вход. **Ожидали** отказ с указанием обязательного мода. **Получили** экран `Connection Lost` с текстом ниже. Мир не загрузился.

```text
Mod rejections [FMLMod:OpenComputers{1.8.10}]
```

На сервере:

```text
Client protocol version 2
Client attempting to join with 3 mods : FML@7.10.99.99,Forge@10.13.4.1614,mcp@9.05
Attempting connection with missing mods [OpenComputers|Core, OpenComputers] at CLIENT
Rejecting connection CLIENT: [FMLMod:OpenComputers{1.8.10}]
```

Закрыли клиент и вернули JAR. **Ожидали и получили** исходный SHA-256:

```powershell
if (Test-Path -LiteralPath $clientJar) { throw "CLIENT_JAR_ALREADY_EXISTS=$clientJar" }; Move-Item -LiteralPath $hold -Destination $clientJar -ErrorAction Stop; "CLIENT_OC_RESTORED_SHA256=$((Get-FileHash -LiteralPath $clientJar -Algorithm SHA256).Hash)"
```

```text
CLIENT_OC_RESTORED_SHA256=40DBD0857EFE6EFF0C8B40965A7B98B689BF0B328194DFA1AC458088073376E9
```

**Контракт Horizon-NTM.** До входа в мир согласовать обязательные моды и версии их протоколов. При несовместимости указать мод и причину. При успешном согласовании применить карту ID сервера до использования модовых ID. У сообщения зарегистрировать канал, тип, версию схемы и сторону-получателя. Декодер проверяет формат и размер, обработчик — допустимость операции, мир меняется в серверном контексте. Приёмочные случаи: совпадающий набор проходит; отсутствующий обязательный мод отклоняется с диагностикой; карта сервера применяется до первого пакета, содержащего соответствующий модовый ID. [Регистрация сообщений в FML](https://github.com/MinecraftForge/FML/blob/1.7.10/src/main/java/cpw/mods/fml/common/network/simpleimpl/SimpleNetworkWrapper.java)

## Проверки PR

Ручные прогоны относятся к Forge 1.7.10. Выполнены 23 теста Python-модели S02. Правила Horizon-NTM и их приёмочные случаи описывают требуемую реализацию. Совместимость с Horizon 26.3 в рантайме не проверялась. Команды Cargo неприменимы к этому документационному изменению.

При ревью проверить `git diff --name-only origin/main...HEAD` и содержимое diff. Ожидаемый файл S10 — `docs/contracts/mod-api.md`. Игровые ассеты, JAR, сохранения, токены, приватные данные и декомпилированные исходники в PR исключаются. Статусы CI и code review фиксируются по PR.
