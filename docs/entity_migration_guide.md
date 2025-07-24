# Entity Migration Guide

**Deutsche Version siehe unten / German version see below**

---

# 🇺🇸 English

## 🔄 Entity Migration Overview

Version 1.2.0 introduces a **unified entity naming convention** that ensures unique entity IDs across multiple Lambda installations. This migration is **automatic** and **preserves all sensor history**.

### What Changes

| Before Migration | After Migration | Example |
|------------------|-----------------|---------|
| `ambient_temperature` | `eu08l_ambient_temperature` | Main sensor |
| `hp1_cop_calc` | `eu08l_hp1_cop_calc` | Heat pump sensor |
| `boil1_temp` | `eu08l_boil1_temp` | Boiler sensor |

### What Stays the Same

✅ **Entity ID**: `sensor.eu08l_ambient_temperature` (unchanged)  
✅ **State History**: All historical data preserved  
✅ **Automations**: Continue working without changes  
✅ **Attributes**: All sensor attributes preserved  
✅ **Device Links**: Device associations maintained  
✅ **Area Assignments**: Room assignments preserved  
✅ **Customizations**: User customizations maintained  

## 🚀 Automatic Migration

The migration happens **automatically** when you update to version 1.2.0:

1. **Detection**: Integration detects if migration is needed (Config Entry Version < 2)
2. **Backup**: Creates backup of `lambda_wp_config.yaml`
3. **Migration**: Updates all entity unique_ids to include name_prefix
4. **Conflict Resolution**: Removes duplicate entities that would conflict
5. **Registry Cleanup**: Eliminates old, non-functional entities
6. **Verification**: Logs all migration steps for transparency
7. **Completion**: Updates Config Entry to version 2

### Migration Logs

You can monitor the migration in Home Assistant logs:

```yaml
# Example migration logs
2024-12-19 10:30:15 INFO (MainThread) [custom_components.lambda_heat_pumps] Entity migration completed
2024-12-19 10:30:15 INFO (MainThread) [custom_components.lambda_heat_pumps] Made unique: ambient_temperature → eu08l_ambient_temperature
2024-12-19 10:30:16 INFO (MainThread) [custom_components.lambda_heat_pumps] Config entry updated to version 2
```

## 🔧 Manual Migration (if needed)

If automatic migration fails, you can trigger it manually:

1. **Restart Home Assistant**
2. **Check logs** for migration status
3. **If needed**, remove and re-add the integration

### Manual Migration Steps

```yaml
# 1. Remove integration (preserves entities)
Configuration → Integrations → Lambda Heat Pumps → Remove

# 2. Re-add integration
Configuration → Integrations → Add Integration → Lambda Heat Pumps

# 3. Migration will run automatically
```

## 🏠 Multiple Installations

The new naming convention supports multiple Lambda installations:

### Example: Multiple Locations

| Installation | Name Prefix | Entity Examples |
|--------------|-------------|-----------------|
| Main House | `eu08l` | `eu08l_ambient_temperature` |
| Garage | `garage` | `garage_ambient_temperature` |
| Basement | `basement` | `basement_ambient_temperature` |

### Benefits

✅ **No Conflicts**: Each installation has unique entity IDs  
✅ **Clear Identification**: Easy to identify which installation an entity belongs to  
✅ **Scalable**: Supports unlimited installations  
✅ **Consistent**: All installations follow the same naming pattern  

## 🛡️ Safety Features

### Backup Creation
- **Automatic backup** of `lambda_wp_config.yaml` before migration
- **Backup location**: `lambda_wp_config.yaml.backup`
- **Timestamp**: Backup created with migration timestamp

### Error Handling
- **Conflict detection**: Prevents overwriting existing entities
- **Graceful fallback**: Continues migration even if some entities fail
- **Duplicate cleanup**: Automatically removes conflicting entities
- **Frontend cleanup**: Eliminates "unavailable" entities after migration
- **Comprehensive logging**: All steps logged for troubleshooting

## 🔧 Troubleshooting

### Duplicate Entities After Migration

If you see "unavailable" entities alongside working ones after migration:

1. **Check Migration Logs**: Look for migration completion messages
2. **Restart Home Assistant**: Often resolves display issues
3. **Manual Cleanup**: If needed, use the provided cleanup scripts

### Migration Not Triggered

If migration doesn't run automatically:

1. **Check Config Entry Version**: Should be version 2 after migration
2. **Restart Home Assistant**: Triggers migration if version < 2
3. **Manual Trigger**: Remove and re-add integration if needed

### Entity Conflicts

If you see "Unique ID already in use" errors:

1. **Automatic Resolution**: The migration handles conflicts automatically
2. **Log Review**: Check logs for conflict resolution messages
3. **Manual Intervention**: Rarely needed, but possible if automatic cleanup fails

### Version Tracking
- **Config Entry Version**: Tracks migration status
- **Prevents re-migration**: Won't migrate already migrated installations
- **Future-proof**: Ready for future migrations

## 🔍 Troubleshooting

### Migration Not Running

**Check Config Entry Version:**
```yaml
# In .storage/core.config_entries
{
  "entry_id": "lambda_heat_pumps_...",
  "version": 1,  # ← Needs migration
  "version": 2   # ← Already migrated
}
```

**Enable Debug Logging:**
```yaml
# In configuration.yaml
logger:
  custom_components.lambda_heat_pumps: debug
```

### Migration Errors

**Common Issues:**
1. **Permission errors**: Check file permissions for `lambda_wp_config.yaml`
2. **Disk space**: Ensure sufficient disk space for backups
3. **Entity conflicts**: Check for duplicate unique_ids

**Solutions:**
1. **Restart Home Assistant** and try again
2. **Check logs** for specific error messages
3. **Manual migration** if automatic fails

### Verification

**Check Migration Success:**
1. **Entity Registry**: Verify unique_ids include name_prefix
2. **State History**: Confirm historical data is preserved
3. **Automations**: Test that automations still work
4. **Logs**: Look for "migration completed" messages

## 📋 Migration Checklist

- [ ] **Backup created** before migration
- [ ] **All entities migrated** to new naming convention
- [ ] **State history preserved** for all sensors
- [ ] **Automations working** without changes
- [ ] **Config entry version** updated to 2
- [ ] **No duplicate entities** created
- [ ] **Logs show successful completion**

---

# 🇩🇪 Deutsch

## 🔄 Entity-Migration Übersicht

Version 1.2.0 führt eine **einheitliche Entity-Namenskonvention** ein, die eindeutige Entity-IDs über mehrere Lambda-Installationen hinweg gewährleistet. Diese Migration ist **automatisch** und **erhält alle Sensor-Historie**.

### Was sich ändert

| Vor der Migration | Nach der Migration | Beispiel |
|-------------------|-------------------|----------|
| `ambient_temperature` | `eu08l_ambient_temperature` | Hauptsensor |
| `hp1_cop_calc` | `eu08l_hp1_cop_calc` | Wärmepumpen-Sensor |
| `boil1_temp` | `eu08l_boil1_temp` | Kessel-Sensor |

### Was gleich bleibt

✅ **Entity ID**: `sensor.eu08l_ambient_temperature` (unverändert)  
✅ **State History**: Alle historischen Daten erhalten  
✅ **Automatisierungen**: Funktionieren weiter ohne Änderungen  
✅ **Attributes**: Alle Sensor-Attribute erhalten  
✅ **Device-Links**: Geräte-Verknüpfungen erhalten  
✅ **Area-Zuordnung**: Raum-Zuordnungen erhalten  
✅ **Customizations**: Benutzer-Anpassungen erhalten  

## 🚀 Automatische Migration

Die Migration erfolgt **automatisch** beim Update auf Version 1.2.0:

1. **Erkennung**: Integration erkennt, ob Migration nötig ist (Config Entry Version < 2)
2. **Backup**: Erstellt Backup von `lambda_wp_config.yaml`
3. **Migration**: Aktualisiert alle Entity unique_ids mit name_prefix
4. **Verifikation**: Loggt alle Migrationsschritte für Transparenz
5. **Abschluss**: Aktualisiert Config Entry auf Version 2

### Migrations-Logs

Sie können die Migration in den Home Assistant Logs überwachen:

```yaml
# Beispiel Migrations-Logs
2024-12-19 10:30:15 INFO (MainThread) [custom_components.lambda_heat_pumps] Entity migration completed
2024-12-19 10:30:15 INFO (MainThread) [custom_components.lambda_heat_pumps] Made unique: ambient_temperature → eu08l_ambient_temperature
2024-12-19 10:30:16 INFO (MainThread) [custom_components.lambda_heat_pumps] Config entry updated to version 2
```

## 🔧 Manuelle Migration (falls nötig)

Falls die automatische Migration fehlschlägt, können Sie sie manuell auslösen:

1. **Home Assistant neu starten**
2. **Logs prüfen** für Migrationsstatus
3. **Falls nötig**, Integration entfernen und neu hinzufügen

### Manuelle Migrationsschritte

```yaml
# 1. Integration entfernen (erhält Entities)
Konfiguration → Integrationen → Lambda Heat Pumps → Entfernen

# 2. Integration neu hinzufügen
Konfiguration → Integrationen → Integration hinzufügen → Lambda Heat Pumps

# 3. Migration läuft automatisch
```

## 🏠 Mehrere Installationen

Die neue Namenskonvention unterstützt mehrere Lambda-Installationen:

### Beispiel: Mehrere Standorte

| Installation | Name Prefix | Entity-Beispiele |
|--------------|-------------|------------------|
| Hauptgebäude | `eu08l` | `eu08l_ambient_temperature` |
| Garage | `garage` | `garage_ambient_temperature` |
| Keller | `basement` | `basement_ambient_temperature` |

### Vorteile

✅ **Keine Konflikte**: Jede Installation hat eindeutige Entity-IDs  
✅ **Klare Identifikation**: Einfach zu erkennen, zu welcher Installation eine Entity gehört  
✅ **Skalierbar**: Unterstützt unbegrenzte Installationen  
✅ **Konsistent**: Alle Installationen folgen dem gleichen Namensmuster  

## 🛡️ Sicherheitsfeatures

### Backup-Erstellung
- **Automatisches Backup** von `lambda_wp_config.yaml` vor Migration
- **Backup-Ort**: `lambda_wp_config.yaml.backup`
- **Zeitstempel**: Backup mit Migrations-Zeitstempel erstellt

### Fehlerbehandlung
- **Konflikt-Erkennung**: Verhindert Überschreiben bestehender Entities
- **Graceful Fallback**: Setzt Migration fort, auch wenn einige Entities fehlschlagen
- **Umfassendes Logging**: Alle Schritte für Troubleshooting geloggt

### Versions-Tracking
- **Config Entry Version**: Verfolgt Migrationsstatus
- **Verhindert Re-Migration**: Migriert bereits migrierte Installationen nicht erneut
- **Zukunftssicher**: Bereit für zukünftige Migrationen

## 🔍 Troubleshooting

### Migration läuft nicht

**Config Entry Version prüfen:**
```yaml
# In .storage/core.config_entries
{
  "entry_id": "lambda_heat_pumps_...",
  "version": 1,  # ← Migration nötig
  "version": 2   # ← Bereits migriert
}
```

**Debug-Logging aktivieren:**
```yaml
# In configuration.yaml
logger:
  custom_components.lambda_heat_pumps: debug
```

### Migrationsfehler

**Häufige Probleme:**
1. **Berechtigungsfehler**: Dateiberechtigungen für `lambda_wp_config.yaml` prüfen
2. **Festplattenspeicher**: Ausreichend Speicherplatz für Backups sicherstellen
3. **Entity-Konflikte**: Auf doppelte unique_ids prüfen

**Lösungen:**
1. **Home Assistant neu starten** und erneut versuchen
2. **Logs prüfen** für spezifische Fehlermeldungen
3. **Manuelle Migration** falls automatische fehlschlägt

### Verifikation

**Migrationserfolg prüfen:**
1. **Entity Registry**: Verifizieren, dass unique_ids name_prefix enthalten
2. **State History**: Bestätigen, dass historische Daten erhalten sind
3. **Automatisierungen**: Testen, dass Automatisierungen weiter funktionieren
4. **Logs**: Nach "migration completed" Nachrichten suchen

## 📋 Migrations-Checkliste

- [ ] **Backup erstellt** vor Migration
- [ ] **Alle Entities migriert** zu neuer Namenskonvention
- [ ] **State History erhalten** für alle Sensoren
- [ ] **Automatisierungen funktionieren** ohne Änderungen
- [ ] **Config entry version** auf 2 aktualisiert
- [ ] **Keine doppelten Entities** erstellt
- [ ] **Logs zeigen erfolgreichen Abschluss** 