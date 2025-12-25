# Swing-Trading-Strategie v1.5 (Long-only)

**Zielgruppe:** Einsteiger und fortgeschrittene Einsteiger mit begrenzter Zeit und kleinem Konto (\~1.000 €)\
**Ziel:** Regelbasiertes, reproduzierbares *wachstumsorientiertes* Accountwachstum bei minimalem Entscheidungsaufwand

---

## 0. Zweck des Dokuments

Dieses Dokument definiert **ein vollständiges, geschlossenes Handelssystem**.\
Alle Regeln sind:

- eindeutig definiert
- messbar
- reproduzierbar
- ohne implizite Diskretion

Abweichungen sind **nicht erlaubt**.

---

## 1. Systemidee (Kurzfassung)

Das System handelt **Long-only Swing-Trades** in klaren Aufwärtstrends.

Gehandelt wird **ein einziges Setup**:

- Trend vorhanden
- externe Ursache (Katalysator)
- erhöhte Volatilität
- strukturierter Pullback

Accountwachstum entsteht durch:

- wenige, hochwertige Trades
- konsequentes, *adaptives* Risikomanagement
- größere Gewinner als Verlierer

---

## 2. Märkte & Instrumente

### Zulässig

- Einzelaktien (ungehebelt)
- Index-ETFs (ungehebelt)
- Rohstoffe (Futures oder ungehebelte ETCs/ETNs)

### Nicht zulässig

- gehebelte Produkte
- CFDs
- Optionsscheine / Knock-Outs

**Grundregel:** Kein Instrument mit implizitem Hebel oder Zeitwertverlust.

---

## 3. Zeitebenen

- Trend & Struktur: Daily / 4H
- Entry-Timing: 1H (alternativ 4H)
- Haltedauer: ca. 2–5 Handelstage

---

## 4. Trenddefinition (Marktzulassung)

Ein Markt ist **nur handelbar**, wenn:

- Higher Highs **und** Higher Lows vorliegen
- Bewertung erfolgt **ausschließlich auf Schlusskursbasis**

**Systemregel:**

- Dochte werden ignoriert
- Intrabar-Bewegungen sind irrelevant

Diese Logik gilt für **Trend, Stop und Exit**.

---

## 5. Volatilitätsfilter

Ein Markt ist zulässig, wenn **mindestens eine** Bedingung erfüllt ist:

- ATR(14) > ATR(14)-20T-Durchschnitt
- 5-Tage-Range ≥ 1,3 × vorherige 20-Tage-Range
- Volatilität durch gültigen Katalysator

**Ausschlussfilter (v1.5 – minimal):**

- Kein Trade, wenn das durchschnittliche Volumen während des Pullbacks **größer ist** als das durchschnittliche Volumen der vorherigen Impulsbewegung.

Ohne Volatilität → **kein Trade**.

---

## 6. Katalysator (Pflicht)

Jeder Trade benötigt einen **externen Auslöser**.

### Zulässig

- Unternehmenszahlen
- Makrodaten
- Branchen-/Sektor-News
- Angebots-/Nachfrageschocks

Maximales Alter: **10 Handelstage**.

### Nachweisbare Marktreaktion

Mindestens **eine** Bedingung:

- Tagesrange ≥ 1,5 × ATR(14) **und** Close im oberen Drittel
- Close über letztem relevanten Swing-High (Daily/4H, Close-only)
- Volumen ≥ 1,5 × 20T-Durchschnitt **oder** Tagesclose ≥ +1,2 %

### Klassifikation

- **K1:** ≥ 2 Kriterien
- **K2:** 1 Kriterium

Ohne bestätigte Reaktion → **kein Trade**.

---

## 7. Entry (einziges Setup)

### Pullback

- mindestens 2 Kerzen gegen den Trend
- seitwärts oder leicht abwärts
- kein Close unter letztem Higher Low

**Zusatzregel zur Struktur (v1.5 – minimal):**

- Der Pullback darf maximal **50 %** der vorherigen Impulsstrecke (HL → HH, Close-only) korrigieren.

### Trigger

- Kerze schließt über Hoch der vorherigen Kerze
- Entry per Market zum Close

---

## 8. Risiko- & Positionsmanagement

### Grundsatz

Risiko ist **berechnet**, nicht geschätzt.

### Begriffe

- Equity: aktueller Kontostand
- Risiko%: maximaler Verlust
- Entry: Einstieg (Close)
- Stop: letztes Higher Low (Close)

### Positionsgröße

1. Geldrisiko = Equity × Risiko%
2. Stop-Distanz = |Entry − Stop|
3. Positionsgröße = Geldrisiko / Stop-Distanz

---

## 9. Risikofunktion (zentral, erweitert)

**Risiko% = f(Marktregime, Trade-Qualität, Drawdown, Equity-Phase)**

### 9.1 Basisrisiko

- **1,0 %**

### 9.2 Marktregime-Faktor

| Regime    | Faktor |
| --------- | ------ |
| Defensiv  | 0,5    |
| Neutral   | 1,0    |
| Expansion | 1,5    |

### 9.3 Trade-Qualität

| Katalysator | Faktor |
| ----------- | ------ |
| K2          | 1,0    |
| K1          | 1,2    |

### 9.4 Drawdown-Bremse (prioritär)

- ≥ 5 % Drawdown → **max. 1,0 % Risiko**
- ≥ 10 % Drawdown → **0,5 % Risiko**

Diese Regel **überschreibt alle anderen Faktoren**.

### 9.5 Equity-basierte Risiko-Stufen (Wachstumsmodul)

**Ziel:** Beschleunigtes Wachstum in statistisch positiven Phasen.

- *Equity-High:* Höchster jemals erreichter Kontostand (Close-Basis)

| Equity-Zustand            | Zusatzfaktor |
| ------------------------- | ------------ |
| Unter letztem Equity-High | 1,0          |
| Neues Equity-High ≤ +5 %  | 1,1          |
| Neues Equity-High > +5 %  | 1,25         |

**Regeln:**

- Risikoerhöhung **nur bei neuem Equity-High**
- Bei *jedem* Drawdown → sofort Rückfall auf Faktor 1,0
- Keine schrittweise Erhöhung ohne neues High

### 9.6 Gesamtrisikoberechnung

Risiko% = Basisrisiko × Regime-Faktor × Qualitätsfaktor × Equity-Faktor\
Danach Anwendung der Drawdown-Bremse\
**Hard Cap: max. 2,0 % Risiko pro Trade**

---

## 10. Marktregime – operativ definiert

### Referenzmarkt

- US: S&P 500 (SPX / SPY)
- EU: STOXX 600 (STOXX / SXXP)

### Update

- 1× pro Woche nach Wochenschluss

### Kriterien (Daily, Close-only)

**Expansion**

- HH/HL-Struktur
- Close > SMA(50)
- ATR(14) ≥ ATR-20T-Durchschnitt

**Neutral**

- kein klarer Trend **oder**
- Close zwischen SMA(50) und SMA(200)

**Defensiv**

- LH/LL-Struktur **oder**
- Close < SMA(200)

Regime beeinflusst **nur das Risiko**, nie das Setup.

---

## 11. Erwartungswert-Absicherung

### Annahmen

- Trefferquote: ca. 40–55 %
- Verlust: −1R
- Gewinn: +1,5R bis +3R

### Zwingende Regeln

- Kein Trade gilt als Gewinner unter +1R unrealisiert.
- Nach Erreichen von +1R darf ein Trendbruch **nicht** unter +1R schließen.

---

## 12. Trade-Management

- keine Teilverkäufe
- keine Stop-Verschiebungen

Exit nur bei:

- Stop (Close)
- bestätigtem Trendbruch (Close)

---

## 13. Ausschlussregeln

- kein Trend → kein Trade
- kein Katalysator → kein Trade
- keine Volatilität → kein Trade
- Checkliste unvollständig → kein Trade

---

## 14. Long-only-Regel

Bei Marktregime **Defensiv**:

- **keine neuen Trades**
- Cash = aktive Position

---

## 15. Prozess & Disziplin

- Regelkonformität > Einzeltrade-Ergebnis
- Regeländerungen nur nach statistischer Auswertung
- Ein Teil der Pullbacks wird systembedingt fehlschlagen; diese Trades gelten **nicht** als Regel- oder Analysefehler, sondern als erwartete Kosten der Trendteilnahme (Meta-Regel, kein Setup-Filter). **Begründung:** In einem Trend ist vor dem Einstieg nie sicher erkennbar, ob ein Pullback nur eine Pause oder bereits der Beginn einer Trendwende ist; das System akzeptiert diese Unsicherheit bewusst und begrenzt sie über feste Stops und Risikoregeln.

---

## 16. Zusammenfassung

Dieses System ist:

- vollständig definiert
- einsteigerverständlich
- wachstumsfähig ohne Systembruch
- langfristig skalierbar

**Accountwachstum entsteht durch Disziplin *****und***** intelligente Risikosteuerung.**

