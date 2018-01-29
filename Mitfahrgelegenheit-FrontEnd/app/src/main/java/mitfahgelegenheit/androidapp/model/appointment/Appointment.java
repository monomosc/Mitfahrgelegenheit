package mitfahgelegenheit.androidapp.model.appointment;

import com.google.gson.annotations.SerializedName;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class Appointment
{

	private final int id;

	private final String startLocation;
	private final String targetLocation;

	@SerializedName("startTimeTimestamp") private final long startTime;
	@SerializedName("repeatTime") private final RepeatType repeatType;

	private AppointmentStatus status;
	private int distance = 0;


	// INIT
	public Appointment(
			int id, String startLocation, String targetLocation, long startTime, RepeatType repeatType, AppointmentStatus status)
	{
		this.id = id;
		this.startLocation = startLocation;
		this.targetLocation = targetLocation;
		this.startTime = startTime;
		this.repeatType = repeatType;
		this.status = status;
	}


	// OBJECT
	@Override public boolean equals(Object o)
	{
		if(this == o)
			return true;
		if((o == null) || (getClass() != o.getClass()))
			return false;

		Appointment that = (Appointment) o;

		if(id != that.id)
			return false;

		return true;
	}

	@Override public int hashCode()
	{
		return id;
	}


	@Override public String toString()
	{
		return "Appointment{"+"id='"+id+'\''+", startLocation='"+startLocation+'\''+", targetLocation='"+targetLocation+'\''
				+", startTime="+startTime+", repeatType="+repeatType+", status="+status+'\''+'}';
	}


	// GETTERS
	public String getStartLocation()
	{
		return startLocation;
	}

	public String getTargetLocation()
	{
		return targetLocation;
	}

	public Date getStartTimeAsDate()
	{
		return new Date(startTime*1000);
	}

	public RepeatType getRepeatType()
	{
		return repeatType;
	}

	public int getId()
	{
		return id;
	}

	public int getKmdistance()
	{
		return distance;
	}

	public AppointmentStatus getStatus()
	{
		return status;
	}

	public void addKmDistance(int distanceInKm)
	{
		distance = distanceInKm;
	}

	//Format of the Appointment Information shown in the AppointmentView
	/*0:startLocation / 1:targetLocation / 2:startTime / 3:creatorName / 4:repeatType / 5:id*/
	public List<String> toStringArr()
	{
		List<String> strings = new ArrayList<>();
		strings.add("From: "+startLocation);
		strings.add("To: "+targetLocation);
		strings.add(""+timeToString());
		strings.add("Repeat: "+repeatType);
		strings.add("Status: "+status);

		strings.add(id+"");
		return strings;
	}

	public void changeLifeCycle(AppointmentStatus cycle)
	{
		if(!cycle.equals(null))
		{
			status = cycle;
		}
	}

	public String timeToString()
	{
		Date date = getStartTimeAsDate();
		SimpleDateFormat formatter = new SimpleDateFormat("EEE, dd.MM.yy 'at' HH:mm", Locale.ENGLISH);
		return formatter.format(date);
	}

}
