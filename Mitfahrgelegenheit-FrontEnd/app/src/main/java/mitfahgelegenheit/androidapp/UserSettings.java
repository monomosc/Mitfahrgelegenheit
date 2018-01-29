package mitfahgelegenheit.androidapp;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;

public final class UserSettings
{

	// CONSTANTS
	private static final String REST_URL_KEY = "rest_url";
	private static final String AUTH_TOKEN_KEY = "auth_token";
	private static final String USERNAME_KEY = "username";

	// REFERENCE
	private final SharedPreferences sharedPreferences;


	// INIT
	public static UserSettings load(Activity activity)
	{
		return new UserSettings(activity.getSharedPreferences("restSettings", Context.MODE_PRIVATE));
	}

	private UserSettings(SharedPreferences sharedPreferences)
	{
		this.sharedPreferences = sharedPreferences;
	}


	// GENERAL
	private String readValue(String key)
	{
		return sharedPreferences.getString(key, null);
	}

	private void writeValue(String key, String value)
	{
		Editor editor = sharedPreferences.edit();

		editor.putString(key, value);
		editor.apply();
	}


	// REST URL
	public AbstractURL getRestUrl()
	{
		String urlString = readValue(REST_URL_KEY);
		if(urlString == null)
			return new AbstractURL("");

		return new AbstractURL(urlString);
	}

	public void setRestUrl(String url)
	{
		writeValue(REST_URL_KEY, url);
	}


	// AUTH TOKEN
	public String getAuthToken()
	{
		return readValue(AUTH_TOKEN_KEY);
	}

	public void setAuthToken(String authToken)
	{
		writeValue(AUTH_TOKEN_KEY, authToken);
	}


	// USERNAME
	public String getUsername()
	{
		return readValue(USERNAME_KEY);
	}

	public void setUsername(String username)
	{
		writeValue(USERNAME_KEY, username);
	}

}
