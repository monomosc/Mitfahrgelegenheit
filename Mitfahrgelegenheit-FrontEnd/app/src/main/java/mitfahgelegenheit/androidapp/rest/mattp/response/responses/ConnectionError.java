package mitfahgelegenheit.androidapp.rest.mattp.response.responses;


import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine;
import mitfahgelegenheit.androidapp.util.MyOptional;

public class ConnectionError<T> extends RequestResponse<T>
{

	private final String errorMessage;

	public ConnectionError(String errorMessage)
	{
		this.errorMessage = errorMessage;
	}


	// OBJECT
	@Override public String toString()
	{
		return "CONNECTION_ERROR: "+errorMessage;
	}


	// GETTERS
	@Override public MyOptional<StatusLine> getStatusLine()
	{
		return MyOptional.empty();
	}

	@Override public MyOptional<T> getContent()
	{
		return MyOptional.empty();
	}

	@Override public MyOptional<String> getErrorMessage()
	{
		return MyOptional.ofNullable(errorMessage);
	}

}
