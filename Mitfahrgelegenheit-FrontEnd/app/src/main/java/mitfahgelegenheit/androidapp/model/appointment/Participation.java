package mitfahgelegenheit.androidapp.model.appointment;

import com.google.gson.annotations.SerializedName;

public class Participation
{

	@SerializedName("id") private final int userId;
	private final int appointmentId;

	@SerializedName("drivingLevel") private final ParticipationType participationType;
	private final int maximumPassengers;


	// INIT
	public Participation(int userId, int appointmentId, ParticipationType participationType, int maximumPassengers)
	{
		this.userId = userId;
		this.appointmentId = appointmentId;
		this.participationType = participationType;
		this.maximumPassengers = maximumPassengers;
	}


	// OBJECT
	@Override public boolean equals(Object o)
	{
		if(this == o)
			return true;
		if((o == null) || (getClass() != o.getClass()))
			return false;

		Participation that = (Participation) o;

		if(userId != that.userId)
			return false;
		if(appointmentId != that.appointmentId)
			return false;

		return true;
	}

	@Override public int hashCode()
	{
		int result = userId;
		result = (31*result)+appointmentId;
		return result;
	}

	@Override public String toString()
	{
		return "Participation{"+"userId="+userId+", appointmentId="+appointmentId+", participationType="+participationType
				+", maximumPassengers="+maximumPassengers+'}';
	}


	// GETTERS
	public int getUserId()
	{
		return userId;
	}

	public int getAppointmentId()
	{
		return appointmentId;
	}

	public ParticipationType getParticipationType()
	{
		return participationType;
	}

	public int getMaximumPassengers()
	{
		return maximumPassengers;
	}


	// PARTICIPATION TYPE
	public enum ParticipationType
	{

		@SerializedName("1")WILL_DRIVE(1, "Will drive"),
		@SerializedName("2")COULD_DRIVE(2, "Could drive"),
		@SerializedName("0")NO_CAR(0, "No car");


		public final int intValue;
		public final String displayName;


		// INIT
		ParticipationType(int intValue, String displayName)
		{
			this.intValue = intValue;
			this.displayName = displayName;
		}

		public static ParticipationType fromIntValue(int intValue)
		{
			for(ParticipationType participationType : values())
				if(participationType.intValue == intValue)
					return participationType;

			throw new IllegalArgumentException("invalid participation type int value: "+intValue);
		}

	}

}
