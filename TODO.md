# TODO - Lambda Heat Pumps Integration

##  Geplante Verbesserungen für robustere Modbus-Kommunikation

### **1. Retry-Logik in modbus_utils.py** 
- [ ] **Automatische Wiederholung** bei Netzwerkfehlern implementieren
- [ ] **Exponentieller Backoff** (1s, 2s, 3s) für Retry-Delays
- [ ] **Intelligente Fehlererkennung** - nur retrybare Fehler wiederholen
- [ ] **Detailliertes Logging** mit Versuchszählung und Fehlertypen
- [ ] **Konfigurierbare Retry-Parameter** (max_retries, retry_delay)

**Betroffene Funktionen:**
- ead_holding_registers() - 3 Retries, 1s Delay
- write_register() - 2 Retries, 0.5s Delay  
- write_registers() - 2 Retries, 0.5s Delay
- ead_input_registers() - 3 Retries, 1s Delay

**Retrybare Fehlertypen:**
- Timeout / Timed out
- Connection refused / unreachable
- No response / Invalid message
- Host is unreachable
- Network is unreachable

### **2. Verbesserte Fehlerbehandlung im Coordinator** 
- [ ] **Graceful Degradation** bei anhaltenden Verbindungsproblemen
- [ ] **Spezifische Fehlerbehandlung** für verschiedene Modbus-Fehler
- [ ] **Bessere Logging-Struktur** mit Fehlerkategorisierung
- [ ] **Null-Checks** für Modbus-Responses vor Register-Zugriff
- [ ] **Fallback-Werte** für kritische Sensoren bei Ausfällen

**Verbesserungen in _async_update_data():**
- [ ] Retry-Logik für alle Register-Lesevorgänge
- [ ] Warnung statt Error bei einzelnen Register-Fehlern
- [ ] Fortsetzung der Datenabfrage auch bei Teilfehlern
- [ ] Bessere Fehlermeldungen mit Register-Adressen

### **3. Adaptive Update-Intervalle** 
- [ ] **Dynamische Update-Intervalle** basierend auf Verbindungsqualität
- [ ] **Normale Intervalle** (30s) bei guter Verbindung
- [ ] **Langsamere Updates** (5min) bei anhaltenden Problemen
- [ ] **Automatische Wiederherstellung** bei Besserung der Verbindung
- [ ] **Konfigurierbare Schwellenwerte** für Intervall-Anpassung

**Implementierung:**
- [ ] _consecutive_failures Counter hinzufügen
- [ ] _max_failures_before_slowdown (Standard: 3)
- [ ] _slow_update_interval (Standard: 300s)
- [ ] _adjust_update_interval() Methode implementieren

### **4. Verbesserte Verbindungsverwaltung** 
- [ ] **Längere Timeouts** (10s statt Standard)
- [ ] **Connection Retries** (3 Versuche)
- [ ] **Bessere Fehlerbehandlung** bei Verbindungsabbrüchen
- [ ] **Connection Pooling** für effizientere Verbindungen
- [ ] **Automatische Reconnection** bei Verbindungsverlust

**ModbusTcpClient Konfiguration:**
`python
ModbusTcpClient(
    host, port,
    timeout=10,           # Längerer Timeout
    retries=3,            # Connection Retries
    retry_on_empty=True,  # Retry bei leeren Responses
    close_comm_on_error=True,  # Verbindung bei Fehler schließen
    strict=False,         # Weniger strikte Validierung
)
`

### **5. Erweiterte Logging-Funktionen** 
- [ ] **Strukturiertes Logging** mit Fehlerkategorien
- [ ] **Performance-Monitoring** (Lesezeiten, Erfolgsraten)
- [ ] **Debug-Modus** für detaillierte Modbus-Kommunikation
- [ ] **Statistik-Sammlung** für Verbindungsqualität
- [ ] **Warnung bei anhaltenden Problemen**

**Neue Log-Level:**
- WARNING: Retry-Versuche, einzelne Register-Fehler
- ERROR: Kritische Fehler, Verbindungsabbrüche
- DEBUG: Detaillierte Modbus-Kommunikation
- INFO: Verbindungsstatus, Intervall-Anpassungen

### **6. Konfigurationsoptionen** 
- [ ] **Retry-Einstellungen** in Config Flow hinzufügen
- [ ] **Timeout-Konfiguration** für verschiedene Register-Typen
- [ ] **Update-Intervall-Anpassung** bei Problemen
- [ ] **Debug-Modus** für erweiterte Logging
- [ ] **Fehlerbehandlung-Präferenzen** (aggressiv/konservativ)

**Neue Config-Optionen:**
`yaml
modbus_settings:
  max_retries: 3
  retry_delay: 1.0
  connection_timeout: 10
  adaptive_updates: true
  debug_mode: false
`

### **7. Monitoring und Diagnose** 
- [ ] **Connection-Health-Monitoring** implementieren
- [ ] **Register-Success-Rate** Tracking
- [ ] **Response-Time-Monitoring** für Performance
- [ ] **Automatische Diagnose** bei Problemen
- [ ] **Health-Check-Service** für externe Monitoring

**Neue Sensoren:**
- [ ] modbus_connection_status - Verbindungsqualität
- [ ] modbus_success_rate - Erfolgsrate der Register-Lesevorgänge
- [ ] modbus_response_time - Durchschnittliche Antwortzeit
- [ ] modbus_error_count - Anzahl der Fehler pro Stunde

### **8. Dokumentation und Tests** 
- [ ] **Dokumentation** der neuen Retry-Logik
- [ ] **Troubleshooting-Guide** für häufige Probleme
- [ ] **Unit-Tests** für Retry-Mechanismen
- [ ] **Integration-Tests** mit simulierten Netzwerkproblemen
- [ ] **Performance-Tests** für verschiedene Szenarien

##  Prioritäten

### **Hoch (Sofort umsetzen)**
1. Retry-Logik in modbus_utils.py
2. Verbesserte Fehlerbehandlung im Coordinator
3. Adaptive Update-Intervalle

### **Mittel (Nächste Version)**
4. Verbesserte Verbindungsverwaltung
5. Erweiterte Logging-Funktionen
6. Konfigurationsoptionen

### **Niedrig (Zukünftige Versionen)**
7. Monitoring und Diagnose
8. Dokumentation und Tests

##  Implementierungsplan

### **Phase 1: Grundlegende Robustheit**
- [ ] modbus_utils.py mit Retry-Logik
- [ ] Coordinator-Fehlerbehandlung verbessern
- [ ] Adaptive Update-Intervalle

### **Phase 2: Erweiterte Funktionen**
- [ ] Verbesserte Verbindungsverwaltung
- [ ] Erweiterte Logging-Funktionen
- [ ] Konfigurationsoptionen

### **Phase 3: Monitoring & Optimierung**
- [ ] Health-Monitoring implementieren
- [ ] Performance-Optimierungen
- [ ] Umfassende Tests

##  Aktuelle Probleme (aus Log-Analyse)

### **Häufige Fehlertypen:**
- [ ] Connection to (192.168.178.125, 502) failed: timed out
- [ ] Host is unreachable
- [ ] No response received, expected at least 8 bytes (0 received)
- [ ] Invalid Message Fehler
- [ ] Connection unexpectedly closed

### **Betroffene Register:**
- [ ] Register 0-4 (General sensors)
- [ ] Register 100-104 (Heat pump sensors)
- [ ] Register 1000-1019 (Extended sensors)
- [ ] Register 2003, 5001, 5003 (Special sensors)

##  Notizen

- **Kompatibilität**: Alle Änderungen müssen mit pymodbus 2.x und 3.x kompatibel bleiben
- **Performance**: Retry-Logik darf nicht zu erheblichen Verzögerungen führen
- **Backward Compatibility**: Bestehende Konfigurationen müssen weiterhin funktionieren
- **Logging**: Nicht zu viele Log-Einträge bei normalem Betrieb erzeugen

---

**Letzte Aktualisierung:** 2024-12-19  
**Status:** In Planung  
**Zielversion:** 1.3.0
