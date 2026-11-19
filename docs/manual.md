# Manuál konfigurátoru

## 1. Architektura

- `src/konfigurator/assets/config_schema_v1.json` — schéma staršího importního formátu.
- `src/konfigurator/assets/config_schema_v3.json` — výstupní schéma odpovídající aktuálnímu kontraktu kalkulačky.
- `models.py` — dataclassy, `ConfigFile.canonical()` pro round-trip bez metadat.
- `schema.py` — loader + allowlisty.
- `validator.py` — vrstva A (jsonschema) + vrstva B (unknown-key warnings) + semantika (unique, activeProfileId existence).
- `io.py` — atomický zápis `tempfile.mkstemp + os.fsync + os.replace`.
- `workers.py` — QThread pro neblokující IO.
- `ui/` — MainWindow (QTabWidget), ProfileEditorDialog (QScrollArea + GroupBoxy), GlobalSettingsWidget.

## 2. Přenositelný formát

Výstup používá `schemaVersion:3`, `activeProfileId`, `profiles[]` a `globalSettings`. Režim čtečky obrazovky, hlasový výstup a motiv patří globálně, nikoli do profilů. Konfigurátor načítá také v1 a při uložení migruje staré hodnoty hlasu a čtečky z aktivního profilu do globálních nastavení. Zachovává také podporovaná doplňková globální nastavení v3.

Enumy jako stringy, `inverseFormatPreference: "dms"|"decimal"|null` (mapuje `0/1/null`), ranges dle auditu.

## 3. Import v kalkulačce (atomický)

`ConfigImportExport.pickAndImportContract` → `FilePicker.pickFiles` → `jsonDecode` → `validateContract` (A+B) → `ConfigPersistence.saveContractAtomically` (klíč podle verze kontraktu, např. `config_contract_v3`) → `materializeToLegacyKeys` (odvozený cache) → `_applyContractMap` (reload + TTS/theme). Při chybě původní konfigurace zůstane beze změny.

## 4. Kompatibilita

Konfigurátor přijímá v1 a v3; exportuje v3. Verze v2 a budoucí verze jsou odmítnuty. `minVersion` je součástí kompatibility kalkulačky.

## 5. Testy

Python: valid/invalid JSON, chybějící/unknown/type/range, duplicate id, active missing, inverse string, ttsVoice, stats uniqueness, round-trip canonical, unknown ignored, schema parity.
Flutter: stejné + `buildContractFromLegacy` + parity.

## 6. Přístupnost — NVDA pořadí

Hlavní okno: titulek → tlačítka Nový/Otevřít/Uložit/Uložit jako/Zkontrolovat (Tab) → záložky (Ctrl+Tab) → uvnitř záložky GroupBox → label → control (SpinBox/ComboBox/CheckBox) → tlačítka Upravit/Duplikovat atd. → stavový label.
Dialog profilu: titulek „Upravit profil: X“ → Jméno → Identita → Zobrazení (Spiny 0.7-2.5 step 0.1) → Oznamování → formátování úhlů → Uložit (autofocus) → Zrušit. Čtečka, motiv a hlas jsou v záložce Globální. Vše čte NVDA s `accessibleName`.
