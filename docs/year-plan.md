# Jahresplan 2025 – SMART-Wochenplan für regelbasiertes Swing Trading & Trading-System

**Stand:** 20.12.2025\
**Ziel:** Aufbau und Betrieb einer **regelbasierten Swing-Trading-Strategie im echten Markt ab Woche 2**, paralleler Aufbau eines Trading-Systems zur **Datenerhebung, Analyse und algorithmischen Unterstützung** (ohne KI).

**Prämissen (fix):**

- Reales Trading startet **ab 27.12.2025**
- Strategie wird **in Woche 1 finalisiert**, danach nur iterativ optimiert
- Keine KI / kein ML
- Jede Woche hat **konkrete SMART-Ziele** mit überprüfbarem Ergebnis

---

## Woche 1 – Strategie-Finalisierung & Alignment

**Zeitraum:** 20.12.2025 – 26.12.2025

**Ziel (S):** Eine vollständig definierte, von allen Beteiligten verstandene Swing-Trading-Strategie

**Was:**

- Finale Auswahl Markt (z. B. US Stocks), Timeframe, Handelsfrequenz
- Definition genau **eines** Setups inkl. Kontext
- Anpassung an Skill-Profile deiner Freunde

**Wie:**

- Strategie schriftlich ausformulieren
- Gemeinsames Review-Meeting
- Beispiel-Trades durchgehen (Charts)

**Warum:**

- Ab Woche 2 echtes Kapital → keine Experimente

**Messbares Ergebnis:**

- Dokument „Swing-Strategie v1.0“ (Entry, Exit, Risiko, Kontext)

---

## Woche 2 – Start reales Swing Trading

**Zeitraum:** 27.12.2025 – 02.01.2026

**Ziel:** Reales Trading strikt nach Strategie

**Was:**

- Durchführung echter Trades
- Lückenlose Dokumentation

**Wie:**

- Jeder Trade nach Regelwerk
- Logging zunächst manuell

**Warum:**

- Reale Daten sind Grundlage für alles Weitere

**Messbares Ergebnis:**

- ≥5 echte Trades mit vollständigem Log

---

## Woche 3

**Zeitraum:** 03.01.2026 – 09.01.2026

**Ziel:** Regelkonformität überprüfen

**Was:**

- Analyse aller Trades auf Regelverletzungen

**Wie:**

- Post-Trade-Review
- Fehler kategorisieren

**Warum:**

- Frühzeitige Disziplinprobleme erkennen

**Ergebnis:**

- Fehlerliste + erste Optimierungsideen

---

## Woche 4

**Zeitraum:** 10.01.2026 – 16.01.2026

**Ziel:** Trading-Log standardisieren

**Was:**

- Einheitliches Log-Schema definieren

**Wie:**

- Felder festlegen (Setup, Kontext, Fehler)

**Warum:**

- Vergleichbarkeit zwischen Tradern

**Ergebnis:**

- Log-Schema v1.0 (JSON/CSV)

---

## Woche 5

**Zeitraum:** 17.01.2026 – 23.01.2026

**Ziel:** Beginn Systematisierung

**Was:**

- Entscheidung über Systemarchitektur

**Wie:**

- Skizze Services & Datenfluss

**Warum:**

- Vorbereitung Backend-Implementierung

**Ergebnis:**

- Architekturdiagramm v1.0

---

## Woche 6

**Zeitraum:** 24.01.2026 – 30.01.2026

**Ziel:** Datenmodell festlegen

**Was:**

- DB-Schema für Trades & Trader

**Wie:**

- PostgreSQL Tabellen entwerfen

**Warum:**

- Saubere Datenbasis

**Ergebnis:**

- SQL-Schema v1.0

---

## Woche 7

**Zeitraum:** 31.01.2026 – 06.02.2026

**Ziel:** Trade-Logging automatisieren

**Was:**

- Backend zum Erfassen von Trades

**Wie:**

- Spring Boot REST API

**Warum:**

- Reduktion manueller Fehler

**Ergebnis:**

- API mit Create/Read Trades

---

## Woche 8

**Zeitraum:** 07.02.2026 – 13.02.2026

**Ziel:** Multi-Trader-Support

**Was:**

- User-Handling

**Wie:**

- Simple Auth

**Warum:**

- Nutzung durch Freunde

**Ergebnis:**

- Mehrbenutzerfähig

---

## Woche 9

**Zeitraum:** 14.02.2026 – 20.02.2026

**Ziel:** Basis-Statistiken

**Was:**

- Winrate, Expectancy, R

**Wie:**

- SQL + Service Layer

**Warum:**

- Objektives Feedback

**Ergebnis:**

- Statistik-Endpoints

---

## Woche 10

**Zeitraum:** 21.02.2026 – 27.02.2026

**Ziel:** Kontext explizit machen

**Was:**

- Marktphasen definieren

**Wie:**

- Regelbasierte Zustände

**Warum:**

- Grundlage für Algorithmen

**Ergebnis:**

- Kontextdefinition v1.0

---

## Woche 11

**Zeitraum:** 28.02.2026 – 06.03.2026

**Ziel:** Kontext-Tagging

**Was:**

- Kontext je Trade speichern

**Wie:**

- Erweiterung DB & API

**Warum:**

- Kontextanalyse ermöglichen

**Ergebnis:**

- Kontextdaten in Logs

---

## Woche 12

**Zeitraum:** 07.03.2026 – 13.03.2026

**Ziel (SMART):** Systematisch messen, wo Trader vom Regelwerk abweichen und warum

**Was:**

- Alle bisherigen Trades klassifizieren (regelkonform / Abweichung)
- Abweichungen in Typen einteilen (Entry-Timing, Stop, Exit, Kontextfehler)

**Wie:**

- SQL-Queries auf Trade-Logs
- Manuelle Review-Sessions mit Charts

**Warum:**

- Nur messbare Abweichungen lassen sich algorithmisch unterstützen

**Messbares Ergebnis:**

- Tabelle mit Abweichungstypen + Häufigkeit
- Dokument „Human-vs-Rule-Report v1.0"

---

## Woche 13

**Zeitraum:** 14.03.2026 – 20.03.2026

**Ziel (SMART):** Entscheidung, welche Regelteile fix und welche flexibel bleiben

**Was:**

- Analyse, welche Abweichungen Performance verbessern/verschlechtern

**Wie:**

- Gruppierung Trades nach Abweichungstyp
- Vergleich R-Multiples

**Warum:**

- Nicht jede Abweichung ist ein Fehler

**Messbares Ergebnis:**

- Entscheidungsdokument: „Fix vs. Flex Rules"

---

## Woche 14

**Zeitraum:** 21.03.2026 – 27.03.2026

**Ziel (SMART):** Strategie präzisieren ohne Charakter zu verändern

**Was:**

- Anpassung exakt definierter Regeln (keine neuen Setups)

**Wie:**

- Regeltext aktualisieren
- Versionsvergleich v1.0 → v1.1

**Warum:**

- Stabilität vor Automatisierung

**Messbares Ergebnis:**

- Strategie-Dokument v1.1

---

## Woche 15

**Zeitraum:** 28.03.2026 – 03.04.2026

**Ziel (SMART):** Formale Beschreibung des Setups für Code-Umsetzung

**Was:**

- Übersetzung Setup → Pseudocode

**Wie:**

- Entscheidungsbäume
- If/Else-Logik definieren

**Warum:**

- Vorbereitung deterministischer Implementierung

**Messbares Ergebnis:**

- Setup-Pseudocode-Dokument

---

## Woche 16

**Zeitraum:** 04.04.2026 – 10.04.2026

**Ziel (SMART):** Implementierung der Setup-Erkennung als Service

**Was:**

- Regelbasierte Setup-Detection

**Wie:**

- Java Service mit Unit-Tests

**Warum:**

- Algorithmische Assistenz starten

**Messbares Ergebnis:**

- Signal-Service v1.0 (lokal testbar)

---

## Woche 17

**Zeitraum:** 11.04.2026 – 17.04.2026

**Ziel (SMART):** Validierung der Signale gegen reale Trades

**Was:**

- Vergleich: Algorithmus-Signal vs. manuelle Entries

**Wie:**

- Log-Matching

**Warum:**

- False Positives erkennen

**Messbares Ergebnis:**

- Precision/Recall-Übersicht

---

## Woche 18

**Zeitraum:** 18.04.2026 – 24.04.2026

**Ziel (SMART):** Kontextfilter ergänzen

**Was:**

- Regeln für Trend/Volatilität implementieren

**Wie:**

- Context-Validator-Komponente

**Warum:**

- Signale nur im validen Marktumfeld

**Messbares Ergebnis:**

- Kontext-Filter v1.0

---

## Woche 19

**Zeitraum:** 25.04.2026 – 01.05.2026

**Ziel (SMART):** Risk-Logik algorithmisieren

**Was:**

- Positionsgröße & Max-Risk prüfen

**Wie:**

- Deterministische Risk-Engine

**Warum:**

- Fehlerreduktion bei Execution

**Messbares Ergebnis:**

- Risk-Service v1.0

---

## Woche 20

**Zeitraum:** 02.05.2026 – 08.05.2026

**Ziel (SMART):** Pre-Trade-Checks automatisieren

**Was:**

- Blockieren ungültiger Trades

**Wie:**

- Regel-Validator vor Entry

**Warum:**

- Disziplin erzwingen

**Messbares Ergebnis:**

- Pre-Trade-Validation aktiv

---

## Woche 21

**Zeitraum:** 09.05.2026 – 15.05.2026

**Ziel (SMART):** Alerting produktiv einsetzen

**Was:**

- Echtzeit-Benachrichtigungen

**Wie:**

- Event-basierte Alerts

**Warum:**

- Reaktionszeit verbessern

**Messbares Ergebnis:**

- Aktive Alerts im Live-Trading

---

## Woche 22

**Zeitraum:** 16.05.2026 – 22.05.2026

**Ziel (SMART):** Messung des System-Nutzens

**Was:**

- Vergleich Performance mit/ohne Assistenz

**Wie:**

- A/B-Vergleich der Trades

**Warum:**

- System muss Mehrwert liefern

**Messbares Ergebnis:**

- Nutzen-Report v1.0

---

## Woche 23

**Zeitraum:** 23.05.2026 – 29.05.2026

**Ziel (SMART):** Stabilisierung der Algorithmik

**Was:**

- Refactoring Regelcode

**Wie:**

- Tests & Code-Reviews

**Warum:**

- Wartbarkeit

**Messbares Ergebnis:**

- Clean Signal/Risk-Codebase

---

## Woche 24

**Zeitraum:** 30.05.2026 – 05.06.2026

**Ziel (SMART):** Backtesting-Fähigkeit herstellen

**Was:**

- Historische Trades simulieren

**Wie:**

- Replay-Mechanismus

**Warum:**

- Regel-Validierung

**Messbares Ergebnis:**

- Backtest-Modul v1.0

---

## Woche 25

**Zeitraum:** 06.06.2026 – 12.06.2026

**Ziel (SMART):** Abgleich Backtest vs. Realität

**Was:**

- Abweichungen analysieren

**Wie:**

- Side-by-Side-Auswertung

**Warum:**

- Modelltreue prüfen

**Messbares Ergebnis:**

- Backtest-Validierungsreport

---

## Woche 26

**Zeitraum:** 13.06.2026 – 19.06.2026

**Ziel (SMART):** System als festen Trading-Bestandteil etablieren

**Was:**

- Verpflichtende Nutzung aller Checks

**Wie:**

- Prozessdefinition

**Warum:**

- Nachhaltigkeit

**Messbares Ergebnis:**

- Trading ohne System nicht möglich

---

## Woche 27

**Zeitraum:** 20.06.2026 – 26.06.2026

**Ziel (SMART):** Anforderungen für einen rein informations- und empfehlungsbasierten Screener eindeutig festlegen (keine Trade-Vorschläge)

**Was:**

- Klare Abgrenzung: Screener liefert **"Was ist interessant und warum"**, niemals Entry/Exit
- Definition der Output-Artefakte: *Interest Report* statt Trade-Vorschlag
- Festlegung der Risikodarstellung (Unsicherheiten, Gegenargumente, Datenlücken)

**Wie:**

- Workshop mit Fokus auf Entscheidungsfragen (nicht Execution)
- Definition von 5 Kernfragen, die der Screener beantworten muss

**Warum:**

- Trennung von Informationsphase und Entscheidungs-/Executionphase ist systemisch notwendig

**Messbares Ergebnis:**

- Dokument „Screener Scope v1.1 (Advisory-only)“
- Explizite Ausschlussliste (keine Entries, Stops, Sizes)

---

## Woche 28

**Zeitraum:** 27.06.2026 – 03.07.2026

**Ziel (SMART):** Datenquellen für technische, fundamentale und qualitative Informationen festlegen

**Was:**

- Technische Marktdaten (OHLCV)
- Fundamentaldaten (KPIs, Earnings, Valuation-Snapshots)
- Nachrichtenquellen (Zeitungen, Pressemitteilungen)
- Social-Media-Quellen (Twitter/X, Reddit – aggregiert)

**Wie:**

- Quellenliste mit Zugriffsmethode (API, Scraping, Feed)
- Bewertung nach Aktualität, Zuverlässigkeit, Kosten

**Warum:**

- Breite Informationsbasis reduziert einseitige Biases

**Messbares Ergebnis:**

- Dokument „Data Sources v1.0“ mit ≥10 priorisierten Quellen

---

## Woche 29

**Zeitraum:** 04.07.2026 – 10.07.2026

**Ziel (SMART):** Datenmodell für Multi-Source-Informationen entwerfen

**Was:**

- Entities: Instrument, PriceBar, FundamentalSnapshot, NewsItem, SocialMention, IndicatorSnapshot, ScreenerRun

**Wie:**

- ERD erstellen
- Normalisierung + Zeitstempel-Strategie festlegen

**Warum:**

- Unterschiedliche Datenarten müssen vergleichbar und versionierbar sein

**Messbares Ergebnis:**

- ERD + PostgreSQL-Migrationen für neue Entitäten

---

## Woche 30

**Zeitraum:** 11.07.2026 – 17.07.2026

**Ziel (SMART):** Technische Analyse als Informationslayer implementieren

**Was:**

- Trend-Zustände, Volatilitätsregime, Liquiditätsstatus

**Wie:**

- Deterministische Berechnung + tägliche Snapshots

**Warum:**

- Liefert objektiven Marktkontext für menschliche Bewertung

**Messbares Ergebnis:**

- Technischer Kontext pro Instrument abrufbar

---

## Woche 31

**Zeitraum:** 18.07.2026 – 24.07.2026

**Ziel (SMART):** Fundamentalanalyse-Snapshots integrieren

**Was:**

- Basiskennzahlen (Revenue-Wachstum, Margen, Verschuldung, Bewertung)

**Wie:**

- Periodischer Import + Normalisierung

**Warum:**

- Fundamentale Lage beeinflusst Risiko und News-Sensitivität

**Messbares Ergebnis:**

- Aktueller FundamentalSnapshot für ≥80 % des Universums

---

## Woche 32

**Zeitraum:** 25.07.2026 – 31.07.2026

**Ziel (SMART):** Nachrichten-Ingestion & Klassifikation (ohne Sentiment-KI)

**Was:**

- Sammeln von News-Artikeln und Pressemitteilungen
- Regelbasierte Klassifikation (Earnings, M&A, Legal, Macro)

**Wie:**

- Keyword-/Source-basierte Heuristiken

**Warum:**

- Ereignisse liefern Kontext, keine Signale

**Messbares Ergebnis:**

- NewsItem-Datenbank mit Klassifikations-Tag

---

## Woche 33

**Zeitraum:** 01.08.2026 – 07.08.2026

**Ziel (SMART):** Social-Media-Signale aggregieren (Noise-reduziert)

**Was:**

- Erwähnungsfrequenz, Themencluster, ungewöhnliche Aktivität

**Wie:**

- Zähl- und Abweichungslogik (Baseline vs. aktuell)

**Warum:**

- Aufmerksamkeit ist ein Risikofaktor, kein Entry-Signal

**Messbares Ergebnis:**

- SocialActivitySnapshot pro Instrument

---

## Woche 34

**Zeitraum:** 08.08.2026 – 14.08.2026

**Ziel (SMART):** Interest-Score definieren (keine Trade-Score)

**Was:**

- Kombination aus technischer Situation, fundamentaler Lage, News- und Social-Aktivität

**Wie:**

- Transparente Gewichtung + Score-Breakdown

**Warum:**

- Priorisierung ohne Handlungszwang

**Messbares Ergebnis:**

- InterestScore v1.0 inkl. Begründungsfeldern

---

## Woche 35

**Zeitraum:** 15.08.2026 – 21.08.2026

**Ziel (SMART):** Interest Report („Warum anschauen?“) generieren

**Was:**

- Zusammenfassung pro Instrument: Chancen, Risiken, offene Fragen

**Wie:**

- Report-Generator (JSON + Markdown)

**Warum:**

- Mensch oder Bot soll informiert entscheiden, nicht blind handeln

**Messbares Ergebnis:**

- Interest Report für Top 30 Instrumente/Woche

---

## Woche 36

**Zeitraum:** 22.08.2026 – 28.08.2026

**Ziel (SMART):** Screener-Workflow operationalisieren

**Was:**

- Täglicher Ablauf: Datenupdate → Screening → Review

**Wie:**

- Cron-Jobs + Review-Checkliste

**Warum:**

- Konsistenz ist wichtiger als Komplexität

**Messbares Ergebnis:**

- 2 Wochen fehlerfrei laufender Screener-Zyklus

---

## Woche 37

**Zeitraum:** 29.08.2026 – 04.09.2026

**Ziel (SMART):** Risikoindikatoren explizit darstellen

**Was:**

- Volatilitätsanstieg, News-Dichte, Social-Hype, fundamentale Schwächen

**Wie:**

- Regelbasierte RiskFlags

**Warum:**

- Gute Entscheidungen brauchen explizite Gegenargumente

**Messbares Ergebnis:**

- RiskFlags Bestandteil jedes Interest Reports

---

## Woche 38

**Zeitraum:** 05.09.2026 – 11.09.2026

**Ziel (SMART):** Menschliche Nutzung des Screeners messen

**Was:**

- Welche Instrumente werden angesehen, ignoriert, weiterverfolgt?

**Wie:**

- View- & Action-Logging

**Warum:**

- Relevanz misst sich an Nutzung, nicht Theorie

**Messbares Ergebnis:**

- Usage-Report v1.0

---

## Woche 39

**Zeitraum:** 12.09.2026 – 18.09.2026

**Ziel (SMART):** Screener-Erkenntnisse mit realen Trades korrelieren

**Was:**

- Welche Interest Reports führten später zu guten/schlechten Trades?

**Wie:**

- Zeitversetzte Korrelation

**Warum:**

- Qualität des Informationssystems bewerten

**Messbares Ergebnis:**

- Correlation-Report v1.0

---

## Woche 40

**Zeitraum:** 19.09.2026 – 25.09.2026

**Ziel (SMART):** Schnittstelle Screener → Trading-System definieren (rein informativ)

**Was:**

- Klare Übergabe: Kontext & Risiko, keine Handlungsanweisung

**Wie:**

- Read-only API

**Warum:**

- Saubere Systemgrenzen

**Messbares Ergebnis:**

- Dokumentierte API + Beispielresponse

---

## Woche 41

**Zeitraum:** 26.09.2026 – 02.10.2026

**Ziel (SMART):** Stabilität & Datenlatenz der Informationspipeline prüfen

**Was:**

- Aktualität der Daten messen

**Wie:**

- SLA-Checks pro Datenquelle

**Warum:**

- Veraltete Information ist gefährlicher als keine

**Messbares Ergebnis:**

- Data-Latency-Report + SLA-Grenzen

---

## Woche 42

**Zeitraum:** 03.10.2026 – 09.10.2026

**Ziel (SMART):** Review & Schärfung der Informationslogik

**Was:**

- Entfernen irrelevanter Signale
- Nachschärfen von RiskFlags

**Wie:**

- Review der letzten 6 Wochen Reports

**Warum:**

- Informationsdichte optimieren

**Messbares Ergebnis:**

- Screener v1.1 mit dokumentierten Änderungen

---

## Woche 43

**Zeitraum:** 10.10.2026 – 16.10.2026

**Ziel (SMART):** Monitoring/Observability für Trading-System einführen

**Was:**

- Logging, Metrics, Error Alerts

**Wie:**

- Structured Logs + Healthchecks

**Warum:**

- Produktiver Betrieb braucht Sichtbarkeit

**Messbares Ergebnis:**

- Monitoring-Dashboard (minimal) + Alarm bei Job-Failures

---

## Woche 44

**Zeitraum:** 17.10.2026 – 23.10.2026

**Ziel (SMART):** CI/CD erweitern: Testabdeckung und Release-Prozess

**Was:**

- Pipeline: lint/tests/build/docker

**Wie:**

- Quality Gates (Tests müssen grün)

**Warum:**

- Engineering-Standard und langfristige Wartbarkeit

**Messbares Ergebnis:**

- Reproduzierbares Release (Tag → Docker Image → Deploy)

---

## Woche 45

**Zeitraum:** 24.10.2026 – 30.10.2026

**Ziel (SMART):** Screener-UI/Frontend minimal bereitstellen (schnelle Nutzung)

**Was:**

- Liste Top-N, Filter, Decision Pack Ansicht

**Wie:**

- Vite/React minimal, Fokus auf Funktion

**Warum:**

- Usability erhöht Adoption und Datenqualität

**Messbares Ergebnis:**

- UI zeigt aktuellen ScreenerRun + Decision Pack für Kandidaten

---

## Woche 46

**Zeitraum:** 31.10.2026 – 06.11.2026

**Ziel (SMART):** „Strategy Hygiene“: Regelkonformität automatisiert messen

**Was:**

- Regelkonformitäts-Score pro Trader

**Wie:**

- Validator + Report

**Warum:**

- Gute Strategie scheitert häufig an Umsetzung

**Messbares Ergebnis:**

- Wöchentlicher Compliance-Report + Top 3 Ursachen

---

## Woche 47

**Zeitraum:** 07.11.2026 – 13.11.2026

**Ziel (SMART):** Risiko-Management auf Portfolioebene (mehrere Trades gleichzeitig)

**Was:**

- Max Exposure, Korrelations-/Cluster-Regeln (einfach, deterministisch)

**Wie:**

- Portfolio-Risk-Checks vor neuen Trades

**Warum:**

- Swing Trading ist Portfoliomanagement, nicht Einzeltrade-Optimierung

**Messbares Ergebnis:**

- Portfolio-Risk-Validator aktiv + Verstöße geloggt

---

## Woche 48

**Zeitraum:** 14.11.2026 – 20.11.2026

**Ziel (SMART):** Backtesting v1.1: Screener + Setup + Risk als End-to-End-Simulation

**Was:**

- End-to-End Replay: candidates → proposed trades → outcomes (vereinfachtes Modell)

**Wie:**

- Deterministische Simulation ohne Optimierungsschleifen

**Warum:**

- Systemverhalten als Ganzes verstehen

**Messbares Ergebnis:**

- End-to-End Backtest-Run mit Report

---

## Woche 49

**Zeitraum:** 21.11.2026 – 27.11.2026

**Ziel (SMART):** Dokumentation als Produkt: Architektur, Datenmodell, Betrieb

**Was:**

- Dokumentation so schreiben, dass ein Dritter das System aufsetzen kann

**Wie:**

- README + Architektur-Docs + Setup-Skripte

**Warum:**

- Voraussetzung für Teamarbeit, Open Source oder Consulting

**Messbares Ergebnis:**

- „Getting Started“ in ≤30 Minuten möglich

---

## Woche 50

**Zeitraum:** 28.11.2026 – 04.12.2026

**Ziel (SMART):** Strategischer Review: Was bleibt manuell, was wird algorithmisch?

**Was:**

- Review der Reject Reasons (Woche 41) und identifizieren der „letzten manuellen Kontextfaktoren"

**Wie:**

- Pareto-Analyse der Reason Codes

**Warum:**

- Nur die richtigen Teile automatisieren

**Messbares Ergebnis:**

- Entscheidungsdokument „Automation Roadmap v1.0"

---

## Woche 51

**Zeitraum:** 05.12.2026 – 11.12.2026

**Ziel (SMART):** Stabilitätswoche: technische Schulden reduzieren

**Was:**

- Refactoring + Tests + Performance der Jobs

**Wie:**

- Profiling + Optimierung der DB-Queries

**Warum:**

- Produktivität im nächsten Jahr hängt an Stabilität

**Messbares Ergebnis:**

- 10 priorisierte Tech-Debt-Tickets geschlossen

---

## Woche 52

**Zeitraum:** 12.12.2026 – 18.12.2026

**Ziel (SMART):** Jahresabschluss: harte Kennzahlen + nächste Roadmap

**Was:**

- Jahresauswertung Trading + System
- Zieldefinition für 2027

**Wie:**

- Reports: Performance, Compliance, Data Quality, System-Uptime

**Warum:**

- Ohne Abschlussreport gibt es keinen Lerneffekt

**Messbares Ergebnis:**

- Dokument „Year Review 2026" (2–5 Seiten) + Roadmap Q1/2027


