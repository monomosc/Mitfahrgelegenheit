package mitfahgelegenheit.androidapp.model.user;

public class User
{

	private final int id;
	private final int globalAdminStatus;

	private final String username;
	private final String email;
	private final String phoneNumber;


	// INIT
	public User(int id, int globalAdminStatus, String username, String email, String phoneNumber)
	{
		this.id = id;
		this.globalAdminStatus = globalAdminStatus;
		this.username = username;
		this.email = email;
		this.phoneNumber = phoneNumber;
	}


	// OBJECT
	@Override public boolean equals(Object o)
	{
		if(this == o)
			return true;
		if((o == null) || (getClass() != o.getClass()))
			return false;

		User user = (User) o;

		if(id != user.id)
			return false;

		return true;
	}

	@Override public int hashCode()
	{
		return id;
	}

	@Override public String toString()
	{
		return "User{"+"id='"+id+'\''+", globalAdminStatus="+globalAdminStatus+", username='"+username+'\''+", email='"+email+'\''
				+", phoneNumber='"+phoneNumber+'\''+'}';
	}


	// GETTERS
	public int getId()
	{
		return id;
	}

	public String getUsername()
	{
		return username;
	}

	public String getEmail()
	{
		return email;
	}

	public String getPhoneNumber()
	{
		return phoneNumber;
	}

	public int getGlobalAdminStatus()
	{
		return globalAdminStatus;
	}

}
