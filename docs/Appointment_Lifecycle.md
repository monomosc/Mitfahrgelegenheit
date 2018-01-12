# Lebenszyklus eines Appointments - chronologische Reihenfolge
## Zweck des Dokuments

In dieser technischen Dokumentation soll genauer beleuchtet werden, wie der Lebenszyklus eines Appointments (im Sinne der REST_spec.pdf) auszusehen hat.

## Erstellung
Ein Appointment mit jeweiligen Daten (siehe die Spezifikation) wird unter 
```POST/api/appointments```
erstellt. Dies erzeugt intern ein Ereignis, welches eine kurze Zeit vor dem Zeitpunkt des Stattfindens des Appointments ausgelöst wird. Zu diesem Zeitpunkt wird das Anmelden gesperrt.
## Nutzer hinzufügen
Jeder Nutzer kann sich selbst; jeder Administrator jeden unter
```PUT /api/appointments/{appointmentID}/users/{userID}```
hinzufügen. Das ´drivingLevel´-Feld ist zu beachten. Dies erzeugt Zeilen in einer Many-to-Many User-Appointment Relationstabelle. Falls ein Nutzer 'drivinglevel' 1 oder 2 angibt, muss er angeben, wie viele Teilnehmer er transportieren kann. Dies geschieht über das optionale Feld 'maximumPassengers'
## Der Anmeldeschluss
Zum Anmeldeschluss (voraussichtlich 60 Minuten vor dem Appointment) können keine Anmeldungen mehr durchgeführt werden. Zu diesem Zeitpunkt überprüft das System die Konfiguration, also insbesondere ob genug Plätze vorhanden sind. Falls dies der Fall ist wird jetzt auf ```GET /api/appointments/{appointmentID}/final``` die Fahrerverteilung angezeigt.
## Archivieren von Appointments
```GET /api/appointments/unfinished```
zeigt die Appointments, die in der Vergangenheit liegen, die aber noch nicht archiviert sind. Nun muss über einen noch zu definierenden Mechanismus die Archivierung eines Appointments stattfinden. Momentaner Plan liegt bei Anbieten eines neuen Endpoints ```UPDATE /api/appointments/{appointmentID}``` mit neuer Syntax zur Verifikation der tatsächlichen Fahrer. Danach wird das retired-Bit gesetzt und das Appointment als abgeschlossen und unveränderbar gesehen. **Diese Funktionalität ist noch nicht implementiert.**
## Fehlerfall: Zuwenige Fahrer
Falls bei Schließen der Registration kurz vor Stattfinden des Appointments zuwenig Fahrer (einschließlich der KANN-Fahrer) existieren, wird eine Email an alle Administratoren sowie alle Teilnehmer geschrieben, und eine Out-Of-Bounds-Einigung wird erfolderlich. Dazu werden Telefonnummern verteilt. Beim Archivieren des Appointments wird dann eine vollständige Eingabe aller Fahrer nötig. **Diese Funktionalität ist noch nicht implementiert**