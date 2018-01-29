package mitfahgelegenheit.androidapp.model.user;

public final class Credentials
{

	private final String username;
	private final String password;


	// INIT
	public Credentials(String username, String password)
	{
		this.username = username;
		this.password = password;
	}


	// GETTERS
	public String getUsername()
	{
		return username;
	}

	public String getPassword()
	{
		return password;
	}

}
