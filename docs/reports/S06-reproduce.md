# S06 — воспроизведение

Python 3.10+, стандартная библиотека; команды PowerShell из корня репозитория. Нужны существующие инструменты S03 из main и новые collect_s06.py/test_s06_manifest.py.

1. В отдельном каталоге игры создать два независимых мира S06-vanilla-clean / S06-forge-clean в vanilla 1.7.10 и Forge 10.13.4.1614 без пользовательских модов: seed 123456789, Default, structures on, Creative, cheats on, bonus chest off. Зафиксировать реальные версии и происхождение. Первоначальный снимок можно снять до посещения измерений.
2. Для полного набора посетить Nether и End в каждом мире. Полностью завершить клиент/сервер перед копированием.
3. Скопировать миры в отдельные локальные snapshot-каталоги. Никогда не использовать рабочий мир во время записи. Не открывать snapshots игрой; для игрового smoke-test делать ещё одну копию. Пример ниже создаёт уникальную папку, не меняя прошлые результаты.

```powershell
$Ref=Join-Path $env:USERPROFILE 'Documents\horizon-reference'; $Out=Join-Path (Get-Location).Path ('.local\S06\verify-'+(Get-Date -Format 'yyyyMMdd-HHmmss')); New-Item -ItemType Directory -Path $Out -ErrorAction Stop | Out-Null
```

```powershell
Copy-Item -LiteralPath (Join-Path $Ref 'saves\S06-vanilla-clean') -Destination (Join-Path $Out 'vanilla') -Recurse -ErrorAction Stop; Copy-Item -LiteralPath (Join-Path $Ref 'saves\S06-forge-clean') -Destination (Join-Path $Out 'forge') -Recurse -ErrorAction Stop
```

```powershell
python tools/collect_s06.py --world "vanilla=$Out\vanilla" --world "forge=$Out\forge" --out "$Out\manifest.json"; Write-Output "EXIT=$LASTEXITCODE"
```

```powershell
python tools/collect_s06.py --world "vanilla=$Out\vanilla" --world "forge=$Out\forge" --out "$Out\repeat.json"; Write-Output "EXIT=$LASTEXITCODE"
```

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$Out\manifest.json","$Out\repeat.json"
```

Ожидается exit 0, одинаковые JSON-хеши; для полного набора во всех шести измерениях SCANNED, pass_chunks>0 и пустые errors. Суммы чанков и хеши чужого независимо созданного мира не обязаны совпасть с отчётом Zeno. Публичные JSON — метаданные конкретных снимков, не переносимые бинарные фикстуры.

## Синтетика и unit-тесты

```powershell
python -m unittest discover -s tests -p 'test_anvil_1710.py' -v
```

```powershell
python -m unittest discover -s tests -p 'test_s03_*.py' -v
```

```powershell
python -m unittest discover -s tests -p 'test_s06_manifest.py' -v
```

Ожидается 18+9+3 теста, OK. Ноль найденных тестов не считается успехом.

```powershell
python tools/anvil_1710.py fixture "$Out\synthetic\r.0.-1.mca"
```

```powershell
python tools/anvil_1710.py check "$Out\synthetic\r.0.-1.mca"
```

```powershell
python tools/check_s03.py "$Out\synthetic"
```

Ожидается 1 chunks, lossless; один pass_chunk и errors=0. Файл имеет региональные координаты (0,-1) из-за синтетического чанка (3,-2). Тестовый NBT-хеш зафиксирован в test_anvil_1710.py. SHA сжатого региона может зависеть от версии zlib; синтетика не предназначена для открытия как полноценный мир.

JSON level.dat содержит allowlist генераторных полей и имена корневых тегов; регионы — размеры, SHA256, число валидных чанков и счётчики. Полный NBT и данные игроков не экспортируются. Для публичного отчёта всё равно просматривать поля и ошибки; реальные сохранения оставлять в .local или вне Git.

Полные ограничения и результаты: S06-manual-2026-11-17.md. Сборщик нельзя использовать как гарантию идентичности worldgen или полной совместимости движка.
