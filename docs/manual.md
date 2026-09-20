# Manuál konfigurátoru

## 1. Architektura

- `src/konfigurator/assets/config_schema_v1.json` — kanonické schéma (hash musí souhlasit s `Mluvici_kalkulacka/assets/config_schema_v1.json`).
- `models.py` — dataclassy, `ConfigFile.canonical()` pro round-trip bez metadat.
- `schema.py` — loader + allowlisty.
- `validator.py` — vrstva A (jsonschema) + vrstva B (unknown-key warnings) + semantika (unique, activeProfileId existence).
- `io.py` — atomický zápis `tempfile.mkstemp + os.fsync + os.replace`.
- `workers.py` — QThread pro neblokující IO.
- `ui/` — MainWindow (QTabWidget), ProfileEditorDialog (QScrollArea + GroupBoxy), GlobalSettingsWidget.

## 2. Přenositelný formát

Viz `assets/config_schema_v1.json`. `schemaVersion:1`, `activeProfileId`, `profiles[]`, `globalSettings{themeMode,isDegreeMode,defaultMode,statsSummaryOrder,statsComputedOrder,currency,devMode}`, `calculatorCompatibility{minVersion,maxVersion:null}`, `createdAt`, `generator`.

Enumy jako stringy, `inverseFormatPreference: "dms"|"decimal"|null` (mapuje `0/1/null`), ranges dle auditu.

## 3. Import v kalkulačce (atomický)

`ConfigImportExport.pickAndImportContract` → `FilePicker.pickFiles` → `jsonDecode` → `validateContract` (A+B) → `ConfigPersistence.saveContractAtomically` (jeden `setString('config_contract_v1')`) → `materializeToLegacyKeys` (odvozený cache) → `_applyContractMap` (reload + TTS/theme). Při chybě původní `config_contract_v1` beze změny, dialog „Import selhal — původní zachována“, `SnackBar` + `speak`, fokus na klávesnici.

## 4. Kompatibilita

`schemaVersion==1` podporováno, jinak odmítnuto. `minVersion` varováno. Migrace legacy → kontrakt při prvním startu pokud `config_contract_v1` chybí. Legacy klíče zůstávají pro downgrade.

## 5. Testy

Python: valid/invalid JSON, chybějící/unknown/type/range, duplicate id, active missing, inverse string, ttsVoice, stats uniqueness, round-trip canonical, unknown ignored, schema parity.
Flutter: stejné + `buildContractFromLegacy` + parity.

## 6. Přístupnost — NVDA pořadí

Hlavní okno: titulek → tlačítka Nový/Otevřít/Uložit/Uložit jako/Zkontrolovat (Tab) → záložky (Ctrl+Tab) → uvnitř záložky GroupBox → label → control (SpinBox/ComboBox/CheckBox) → tlačítka Upravit/Duplikovat atd. → stavový label.
Dialog profilu: titulek „Upravit profil: X“ → Jméno → Identita → Zobrazení (Spiny 0.7-2.5 step 0.1) → Oznamování → TTS (Rate 0.1-1.0) → Uložit (autofocus) → Zrušit. Vše čte NVDA s `accessibleName`.
