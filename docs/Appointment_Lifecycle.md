# Lebenszyklus eines Appointments - chronologische Reihenfolge
## Zweck des Dokuments

In dieser technischen Dokumentation soll genauer beleuchtet werden, wie der Lebenszyklus eines Appointments (im Sinne der REST_spec.pdf) auszusehen hat.

## Erstellung
Ein Appointment mit jeweiligen Daten (siehe die Spezifikation) wird unter 
´´´POST/api/appointments´´´
erstellt. Dies erzeugt intern Ereignis, welches eine kurze Zeit vor dem Zeitpunkt des Stattfindens des Appointments ausgelöst wird. Zu diesem Zeitpunkt wird das Anmelden gesperrt.
## Nutzer hinzufügen
Jeder Nutzer kann sich selbst; jeder Administrator jeden unter
´´´PUT /api/appointments/{appointmentID}/users/{userID}´´´
hinzufügen. Das ´drivingLevel´-Feld ist zu beachten.