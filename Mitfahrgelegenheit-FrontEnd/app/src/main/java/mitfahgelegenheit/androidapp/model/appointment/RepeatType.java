package mitfahgelegenheit.androidapp.model.appointment;

import com.google.gson.annotations.SerializedName;

public enum RepeatType
{

	@SerializedName("None")NONE("never"),
	@SerializedName("Daily")DAILY("daily"),
	@SerializedName("Weekly")WEEKLY("weekly");


	private final String name;


	RepeatType(String name)
	{
		this.name = name;
	}


	@Override public String toString()
	{
		return name;
	}

}
