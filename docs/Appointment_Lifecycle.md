# Lebenszyklus eines Appointments - chronologische Reihenfolge

## Begriffe

Appointments im SQL-Schema haben das Feld **status**. Es geht um den Status im Lebenszyklus des Appointments. Hier der Python-Code, welcher das klarstellen sollte:
```Python
APPOINTMENT_UNFINISHED = 1
APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE = 2
APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE = 3
APPOINTMENT_LOCKED_NO_FIT = 4
APPOINTMENT_RETIRED = 5
```
## Zweck des Dokuments

In dieser technischen Dokumentation soll genauer beleuchtet werden, wie der Lebenszyklus eines Appointments (im Sinne der REST_spec.pdf) auszusehen hat.

## Erstellung
Ein Appointment mit jeweiligen Daten (siehe die Spezifikation) wird unter 
```
POST/api/appointments
```
erstellt. Dies erzeugt intern ein Ereignis, einem *Cronjob* nicht unähnlich, welches eine kurze Zeit vor dem Zeitpunkt des Stattfindens des Appointments ausgelöst wird. Zu diesem Zeitpunkt wird das Anmelden gesperrt.

## Nutzer hinzufügen
Jeder Nutzer kann sich selbst; jeder Administrator jeden unter
```
PUT /api/appointments/{appointmentID}/users/{userID}
```
hinzufügen. Das ´drivingLevel´-Feld ist zu beachten. Dies erzeugt Zeilen in einer Many-to-Many User-Appointment Relationstabelle. Falls ein Nutzer 'drivinglevel' 1 oder 2 angibt, muss er angeben, wie viele Teilnehmer er transportieren kann. Dies geschieht über das optionale Feld 'maximumPassengers'
## Der Anmeldeschluss
Zum Anmeldeschluss (voraussichtlich 60 Minuten vor dem Appointment) können keine Anmeldungen mehr durchgeführt werden. Zu diesem Zeitpunkt überprüft das System die Konfiguration, also insbesondere ob genug Plätze vorhanden sind. Falls dies der Fall ist wird jetzt auf 
```
GET /api/appointments/{appointmentID}/drivingDistribution
```
die Fahrerverteilung angezeigt. Sie liegt in der Form einer assoziativen Liste vor:
```json
{
    1 : [1,2,3,4],
    6 : [6,7,9],
    ...
}
```
Ebenfalls zu diesem Zeitpunkt wird der Status angepasst - das Status-Feld in der SQL-Datenbank wird einen der folgenden drei Zustände annehmen:
```Python
APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE = 2
APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE = 3
APPOINTMENT_LOCKED_NO_FIT = 4
```
Außerdem, um Fehler anzuzeigen, existiert noch der Zustand
```Python
APPOINTMENT_BROKEN = 6
```

## Archivieren von Appointments

### Anzeigen aller noch nicht archivierten Appointments
**DIESE FUNKTION IST NOCH NICHT IMPLEMENTIERT**
```
GET /api/appointments/unfinished
```
zeigt die Appointments, die in der Vergangenheit liegen, die aber noch nicht archiviert sind.

### Tatsächliche Archivierung

Unter
```
POST /api/appointments/{appointmentID}/retire
```
mit JSON der Form *{'drivers' : [userid, userid, ...]}* werden Appointments final archiviert. Das **drivers**-Feld im Request dient der Angabe der tatsächlichen Fahrer.

## Fehlerfall: Zuwenige Fahrer
Falls bei Schließen der Registration kurz vor Stattfinden des Appointments zuwenig Fahrer (einschließlich der KANN-Fahrer) existieren, wird eine Email an alle Administratoren sowie alle Teilnehmer geschrieben, und eine Out-Of-Bounds-Einigung wird erfolderlich. Dazu werden Telefonnummern verteilt. Beim Archivieren des Appointments wird dann eine vollständige Eingabe aller Fahrer nötig. **Diese Funktionalität ist noch nicht implementiert**