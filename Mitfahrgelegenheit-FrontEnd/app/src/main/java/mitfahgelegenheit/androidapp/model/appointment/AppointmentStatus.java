package mitfahgelegenheit.androidapp.model.appointment;

import com.google.gson.annotations.SerializedName;

public enum AppointmentStatus
{

	@SerializedName("APPOINTMENT_UNFINISHED")UNFINISHED("open"),
	@SerializedName("APPOINTMENT_LOCKED_EVERYONE_FITS_DEFINITE")LOCKED_FIT_DEFINITE("closed"),
	@SerializedName("APPOINTMENT_LOCKED_EVERYONE_FITS_POSSIBLE")LOCKED_FIT_POSSIBLE("closed"),
	@SerializedName("APPOINTMENT_LOCKED_NO_FIT")LOCKED_NO_FIT("closed"),
	@SerializedName("APPOINTMENT_RETIRED")RETIRED("archived"),
	@SerializedName("APPOINTMENT_BROKEN")BROKEN("ERROR");


	private final String displayName;


	// INIT
	AppointmentStatus(String displayName)
	{
		this.displayName = displayName;
	}


	// OBJECT
	@Override public String toString()
	{
		return displayName;
	}

}
