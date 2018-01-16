#import Interne_Entities

APPOINTMENT_UNFINISHED = 1
APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE = 2
APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE = 3
APPOINTMENT_LOCKED_NO_FIT = 4
APPOINTMENT_RETIRED = 5
APPOINTMENT_BROKEN = 6

def getAppointmentStatusString(status):
    returnString = {
        1 : "APPOINTMENT_UNFINISHED",
        2 : "APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE",
        3 : "APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE",
        4 : "APPOINTMENT_LOCKED_NO_FIT",
        5 : "APPOINTMENT_RETIRED",
        6 : "APPOINTMENT_BROKEN"
    }
    return returnString[status]