# Cleanup Scripts Documentation

**Deutsche Version siehe unten / German version see below**

---

# 🇺🇸 English

## Overview

This document describes the cleanup scripts provided for resolving entity conflicts after migration to version 1.2.0.

## Available Scripts

### 1. `cleanup_duplicates.py`

**Purpose**: Removes entities with duplicate `unique_id` values.

**Usage**:
```bash
python cleanup_duplicates.py
```

**What it does**:
- Finds Lambda entities with identical `unique_id` values
- Keeps the first entity, removes the rest
- Creates a backup before making changes
- Reports the number of removed entities

### 2. `cleanup_old_entities.py`

**Purpose**: Removes old entities that don't use the new naming convention.

**Usage**:
```bash
python cleanup_old_entities.py
```

**What it does**:
- Identifies entities without the `eu08l_` prefix in `unique_id`
- Removes these old, non-functional entities
- Creates a backup before making changes
- Reports the number of removed entities

## When to Use

### Use `cleanup_duplicates.py` when:
- You see "Unique ID already in use" errors in logs
- Multiple entities have the same `unique_id`
- Migration reports conflicts

### Use `cleanup_old_entities.py` when:
- You see "unavailable" entities in the frontend
- Old entities persist alongside new ones
- Migration completed but old entities remain

## Safety Features

### Automatic Backups
Both scripts create automatic backups:
- **Location**: `.storage/core.entity_registry.backup`
- **Format**: JSON with all original data
- **Recovery**: Can be restored if needed

### Safe Operations
- **Read-only first**: Scripts analyze before making changes
- **Detailed logging**: All operations are logged
- **Confirmation**: Shows what will be removed before doing it

## Recovery

If you need to restore from backup:

1. **Stop Home Assistant**
2. **Restore backup**:
   ```bash
   cp .storage/core.entity_registry.backup .storage/core.entity_registry
   ```
3. **Restart Home Assistant**

## Example Output

### cleanup_duplicates.py
```
Lade Entity Registry von: C:\Users\gj\OneDrive\dockers\config\.storage\core.entity_registry
Gefundene Lambda Entities: 121
ℹ️ Keine Duplikate gefunden
```

### cleanup_old_entities.py
```
Lade Entity Registry von: C:\Users\gj\OneDrive\dockers\config\.storage\core.entity_registry
Gefundene Lambda Entities: 121
Neue Entities (mit eu08l_): 111
Alte Entities (ohne eu08l_): 10
  ENTFERNEN: sensor.boil1_error_number (unique_id: boil1_error_number)
  ENTFERNEN: sensor.boil1_operating_state (unique_id: boil1_operating_state)
  ...
✅ Cleanup abgeschlossen: 10 alte Entities entfernt
```

---

# 🇩🇪 Deutsch

## Übersicht

Dieses Dokument beschreibt die Cleanup-Skripte, die zur Lösung von Entity-Konflikten nach der Migration auf Version 1.2.0 bereitgestellt werden.

## Verfügbare Skripte

### 1. `cleanup_duplicates.py`

**Zweck**: Entfernt Entities mit doppelten `unique_id` Werten.

**Verwendung**:
```bash
python cleanup_duplicates.py
```

**Was es macht**:
- Findet Lambda Entities mit identischen `unique_id` Werten
- Behält die erste Entity, entfernt die restlichen
- Erstellt ein Backup vor den Änderungen
- Meldet die Anzahl der entfernten Entities

### 2. `cleanup_old_entities.py`

**Zweck**: Entfernt alte Entities, die nicht das neue Namensschema verwenden.

**Verwendung**:
```bash
python cleanup_old_entities.py
```

**Was es macht**:
- Identifiziert Entities ohne `eu08l_` Prefix in der `unique_id`
- Entfernt diese alten, nicht funktionierenden Entities
- Erstellt ein Backup vor den Änderungen
- Meldet die Anzahl der entfernten Entities

## Wann zu verwenden

### Verwende `cleanup_duplicates.py` wenn:
- Du "Unique ID already in use" Fehler in den Logs siehst
- Mehrere Entities die gleiche `unique_id` haben
- Die Migration Konflikte meldet

### Verwende `cleanup_old_entities.py` wenn:
- Du "nicht verfügbar" Entities im Frontend siehst
- Alte Entities neben neuen bestehen bleiben
- Die Migration abgeschlossen ist, aber alte Entities verbleiben

## Sicherheitsfunktionen

### Automatische Backups
Beide Skripte erstellen automatische Backups:
- **Ort**: `.storage/core.entity_registry.backup`
- **Format**: JSON mit allen ursprünglichen Daten
- **Wiederherstellung**: Kann bei Bedarf wiederhergestellt werden

### Sichere Operationen
- **Zuerst lesend**: Skripte analysieren vor Änderungen
- **Detailliertes Logging**: Alle Operationen werden protokolliert
- **Bestätigung**: Zeigt was entfernt wird, bevor es gemacht wird

## Wiederherstellung

Falls du von einem Backup wiederherstellen musst:

1. **Home Assistant stoppen**
2. **Backup wiederherstellen**:
   ```bash
   cp .storage/core.entity_registry.backup .storage/core.entity_registry
   ```
3. **Home Assistant neu starten** 