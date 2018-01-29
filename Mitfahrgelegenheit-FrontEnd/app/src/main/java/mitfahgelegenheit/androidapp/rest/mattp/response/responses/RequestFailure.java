package mitfahgelegenheit.androidapp.rest.mattp.response.responses;


import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine;
import mitfahgelegenheit.androidapp.rest.result.MessageWrapper;
import mitfahgelegenheit.androidapp.rest.serialization.GsonUtil;
import mitfahgelegenheit.androidapp.util.MyOptional;
import mitfahgelegenheit.androidapp.util.PHR;

public class RequestFailure<T> extends RequestResponse<T>
{

	private final StatusLine statusLine;
	private final String errorMessage;


	// INIT
	public RequestFailure(StatusLine statusLine, String errorMessage)
	{
		this.statusLine = statusLine;
		this.errorMessage = errorMessage;
	}


	// OBJECT
	@Override public String toString()
	{
		return PHR.r("FAILURE | {}: {}", statusLine, errorMessage);
	}


	// GETTERS
	@Override public MyOptional<StatusLine> getStatusLine()
	{
		return MyOptional.of(statusLine);
	}

	@Override public MyOptional<T> getContent()
	{
		return MyOptional.empty();
	}

	@Override public MyOptional<String> getErrorMessage()
	{
		try
		{
			MessageWrapper messageWrapper = GsonUtil.get().fromJson(errorMessage, MessageWrapper.class);
			return MyOptional.ofNullable(messageWrapper.getMessage());
		}
		catch(RuntimeException ignored)
		{
			return MyOptional.ofNullable(errorMessage);
		}
	}

}
