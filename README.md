# Konfigurátor mluvící kalkulačky

Desktopová aplikace pro Windows (Python 3.13+ + PyQt6) pro pohodlné nastavení všech konfigurovatelných parametrů **Mluvící kalkulačky** na PC a export do přenositelného souboru `mluvici_kalkulacka_config_v3.json`, který lze importovat přímo ve Flutter aplikaci. Starší kontrakt v1 lze otevřít a při uložení se převede na v3.

## Spuštění

```powershell
py -m pip install -e .
py -m konfigurator.app
# nebo
python -m konfigurator.app
```

Požadavky: Python 3.13+, PyQt6 6.7+, jsonschema, packaging, accessible-output2 (jen Windows, pro hlasový výstup). Žádný Tkinter/wx/Kivy/web.

## Vytvoření konfigurace

1. Spusťte konfigurátor.
2. Záložka **Profily**: upravte existující (standard/blind/lowvision), duplikujte, vytvářejte nové, přejmenujte, smažte (vestavěné nelze smazat), nastavte aktivní profil.
3. Editor profilu (GroupBoxy): nastavení zobrazení a oznamování konkrétního profilu. Čtečka obrazovky, hlasový výstup a motiv aplikace jsou v **Globálním nastavení** stejně jako v aktuální kalkulačce.
4. Záložka **Globální**: téma, režim čtečky, hlasový výstup, výchozí režim, pořadí statistiky (přesun šipkami), měna, vývojářský režim.
5. **Zkontrolovat** — validace proti schématu v3 (vrstva A JSON + vrstva B unknown-key warnings); při otevření se stále validují i soubory v1.
6. **Uložit jako…** → `mluvici_kalkulacka_config_v3.json`.

## Přenos do telefonu

- USB, e-mail, cloud, sdílení — soubor je čistý JSON.
- V kalkulačce: **Více možností → Importovat konfiguraci (kontrakt)** → vyberte soubor → validace → atomický import.
- Při nevalidní/unknown-version chybná konfigurace je odmítnuta, původní zachována, uživatel dostane dialog.

## Export z kalkulačky

V kalkulačce **Více možností → Exportovat konfiguraci (kontrakt)** → soubor se nasdílí (SharePlus) → lze upravit v konfigurátoru a znovu importovat. Oba směry stejný kontrakt.

## Verze schématu

- `schemaVersion = 3` při exportu. Konfigurátor načítá v1 a v3; v1 se migruje do v3, v2 a budoucí verze se odmítají.
- `calculatorCompatibility.minVersion` — konfigurátor zapisuje `11.5.0`, kalkulačka varuje při nekompatibilitě.
- `createdAt`/`generator` jsou dynamická metadata, ignorují se při `canonicalize()` porovnání (round-trip test).
- Neznámá pole → warning + ignorování (forward-compat), známá pole striktně validována.

## Přidání nového nastavení

1. Rozšiřte `assets/config_schema_v3.json` (přidejte property, enum, range).
2. Aktualizujte `src/konfigurator/models.py` a odpovídající kontrakt/validátor kalkulačky.
3. Aktualizujte `GlobalSettingsWidget` / `ProfileEditorDialog`.
4. Zkopírujte schéma do obou repozitářů a ověřte hash (`pytest tests/test_schema_parity.py`, `flutter test test/schema_parity_test.dart`).

## Přístupnost

- Kompletně ovladatelné klávesnicí: `Tab`/`Shift+Tab`, `Enter`/`Space`, šipky, `Esc`.
- Všechny widgety mají `setAccessibleName`, správný `tabOrder`, GroupBoxy, standardní Qt widgety.
- Dialog po otevření fokusuje první pole, po zavření vrací fokus na volající tlačítko.
- Dlouhé operace (načtení/validace/uložení) běží v `QThread` (signály/sloty), UI nezamrzá.
- Tiché akce bez dialogu (přejmenovat, smazat, duplikovat, nastavit aktivní profil, změny sad a složek) jsou navíc potvrzeny hlasem: když běží čtečka obrazovky, text předá jejímu vlastnímu výstupu, když ne, mluví systémový hlas Windows (knihovna `accessible-output2`, modul `konfigurator/announce.py`).
- Ve Flutteru: `Semantics`, `liveRegion`, `header`, návrat fokusu po importu, `SnackBar` + `speak`.

## Testy

```powershell
py -m pytest tests -q
flutter test
flutter analyze
```

Viz `docs/manual.md` pro detailní popis kontraktu a NVDA pořadí čtení.
