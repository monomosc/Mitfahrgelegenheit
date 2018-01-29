package mitfahgelegenheit.androidapp.rest.serialization;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public final class GsonUtil
{

	// REFERENCES
	private static Gson gson = null;


	// INIT
	private GsonUtil() {}


	public static synchronized Gson get()
	{
		if(gson == null)
			gson = new GsonBuilder().create();

		return gson;
	}

}
