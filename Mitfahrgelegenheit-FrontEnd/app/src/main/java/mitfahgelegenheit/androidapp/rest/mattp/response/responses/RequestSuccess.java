package mitfahgelegenheit.androidapp.rest.mattp.response.responses;


import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine;
import mitfahgelegenheit.androidapp.util.MyOptional;
import mitfahgelegenheit.androidapp.util.PHR;

public class RequestSuccess<T> extends RequestResponse<T>
{

	private final StatusLine statusLine;
	private final T body;


	// INIT
	public RequestSuccess(StatusLine statusLine, T body)
	{
		this.statusLine = statusLine;
		this.body = body;
	}


	// OBJECT
	@Override public String toString()
	{
		return PHR.r("SUCCESS | {}: {}", statusLine, body);
	}


	// GETTERS
	@Override public MyOptional<StatusLine> getStatusLine()
	{
		return MyOptional.of(statusLine);
	}

	@Override public MyOptional<T> getContent()
	{
		return MyOptional.ofNullable(body);
	}

	@Override public MyOptional<String> getErrorMessage()
	{
		return MyOptional.empty();
	}

}
