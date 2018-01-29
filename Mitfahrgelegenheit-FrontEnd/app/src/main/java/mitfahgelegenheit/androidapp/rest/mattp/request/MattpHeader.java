package mitfahgelegenheit.androidapp.rest.mattp.request;

public class MattpHeader
{

	private final String key;
	private final String value;


	// INIT
	public MattpHeader(String key, String value)
	{
		validateKey(key);
		validateValue(value);

		this.key = key;
		this.value = value;
	}

	private void validateKey(String key)
	{
		if(key == null)
			throw new IllegalArgumentException("key can't be null");

		if(key.contains(":"))
			throw new IllegalArgumentException("header key can't contain colon (:)");
	}

	private void validateValue(String value)
	{
		if(value == null)
			throw new IllegalArgumentException("value can't be null");
	}


	// GETTERS
	public String getKey()
	{
		return key;
	}

	public String getValue()
	{
		return value;
	}

}
