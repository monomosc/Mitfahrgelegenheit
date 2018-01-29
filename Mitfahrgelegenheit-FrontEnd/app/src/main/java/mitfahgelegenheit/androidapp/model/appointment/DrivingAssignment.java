package mitfahgelegenheit.androidapp.model.appointment;

import com.google.gson.annotations.SerializedName;

import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

public class DrivingAssignment
{

	@SerializedName("status") private final boolean valid;
	@SerializedName("participationList") private final Map<Integer, List<Integer>> participantsByDriver;


	// INIT
	public DrivingAssignment(boolean valid, Map<Integer, List<Integer>> participantsByDriver)
	{
		this.valid = valid;
		this.participantsByDriver = participantsByDriver;
	}


	// GETTERS
	public boolean isValid()
	{
		return valid;
	}

	public int getDriverUserIdOf(int userId)
	{
		if(!isValid())
			throw new IllegalStateException("can't get driver of user in invalid driving assignment");

		for(Entry<Integer, List<Integer>> entry : participantsByDriver.entrySet())
			if(entry.getValue().contains(userId))
				return entry.getKey();

		throw new IllegalArgumentException("user "+userId+" not in driving assignment");
	}

	public int getNumberOfParticipantsOfDriver(int userId)
	{
		if(!isValid())
			throw new IllegalStateException("can't get driver of user in invalid driving assignment");
		List<Integer> participants = participantsByDriver.get(userId);
		if(participants==null){
			throw new IllegalArgumentException("user "+userId+" not in driving assignment");
		}
		return participants.size();
	}
}
