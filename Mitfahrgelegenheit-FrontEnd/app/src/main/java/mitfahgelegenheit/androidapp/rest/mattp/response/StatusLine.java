package mitfahgelegenheit.androidapp.rest.mattp.response;

public class StatusLine
{

	private final String protocolVersion;
	private final int statusCode;
	private final String reasonPhrase;


	// INIT
	public StatusLine(String protocolVersion, int statusCode, String reasonPhrase)
	{
		this.protocolVersion = protocolVersion;
		this.statusCode = statusCode;
		this.reasonPhrase = reasonPhrase;
	}


	// OBJECT
	@Override public String toString()
	{
		return protocolVersion+" "+statusCode+" "+reasonPhrase;
	}


	// GETTERS
	public boolean isSuccess()
	{
		return (statusCode/100) == 2;
	}

}
