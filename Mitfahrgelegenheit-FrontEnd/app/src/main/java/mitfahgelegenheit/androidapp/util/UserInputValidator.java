package mitfahgelegenheit.androidapp.util;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class UserInputValidator
{

	// INIT
	private UserInputValidator() {}


	// VALIDATION
	public static boolean isUserNameValid(CharSequence username)
	{
		return username.length() > 3;
	}

	public static boolean isEmailValid(CharSequence email)
	{
		Matcher matcher = Pattern.compile(
				"^[A-Z0-9ÄÖÜ._%+/\" -]+@(([ÄÖÜA-Z0-9.-]+\\.[A-Z]{2,6})|((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])))$",
				Pattern.CASE_INSENSITIVE).matcher(email);
		return matcher.find();
	}

	public static boolean isPhoneValid(CharSequence phoneNumber)
	{
		return phoneNumber.length() >= 3;
	}

	public static boolean isPasswordValid(CharSequence password)
	{
		return password.length() > 3;
	}

}
