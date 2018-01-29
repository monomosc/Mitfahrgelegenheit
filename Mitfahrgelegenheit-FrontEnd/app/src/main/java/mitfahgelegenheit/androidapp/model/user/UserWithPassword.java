package mitfahgelegenheit.androidapp.model.user;

import mitfahgelegenheit.androidapp.rest.serialization.ByDeserialization;

public final class UserWithPassword extends User
{

	@ByDeserialization private final String password;


	// INIT
	public UserWithPassword(User user, String password)
	{
		super(user.getId(), user.getGlobalAdminStatus(), user.getUsername(), user.getEmail(), user.getPhoneNumber());
		this.password = password;
	}

	public UserWithPassword(int id, int globalAdminStatus, String username, String email, String phoneNumber, String password)
	{
		super(id, globalAdminStatus, username, email, phoneNumber);
		this.password = password;
	}

}
