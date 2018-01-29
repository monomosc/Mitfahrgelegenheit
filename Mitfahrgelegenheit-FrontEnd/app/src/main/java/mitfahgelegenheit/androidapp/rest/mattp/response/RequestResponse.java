package mitfahgelegenheit.androidapp.rest.mattp.response;

import mitfahgelegenheit.androidapp.util.MyOptional;

public abstract class RequestResponse<T>
{

	public boolean isSuccess()
	{
		if(!getStatusLine().isPresent())
			return false;

		return getStatusLine().get().isSuccess();
	}


	public abstract MyOptional<StatusLine> getStatusLine();

	public abstract MyOptional<T> getContent();

	public abstract MyOptional<String> getErrorMessage();

}
