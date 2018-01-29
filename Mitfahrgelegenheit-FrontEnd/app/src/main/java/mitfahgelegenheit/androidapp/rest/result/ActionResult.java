package mitfahgelegenheit.androidapp.rest.result;

public class ActionResult<T>
{

	private final ActionResultType actionResultType;
	private final String message;
	private final String rawErrorReturn;
	private final T value;


	// INIT
	public ActionResult(ActionResultType actionResultType, String message, String rawErrorReturn, T value)
	{
		this.actionResultType = actionResultType;
		this.message = message;
		this.rawErrorReturn = rawErrorReturn;
		this.value = value;
	}


	// OBJECT
	@Override public String toString()
	{
		return "ActionResult{"+"actionResultType="+actionResultType+", message='"+message+'\''+", value="+value+'}';
	}


	// GETTERS
	public boolean isSuccess()
	{
		return actionResultType == ActionResultType.SUCCESS;
	}

	public String getMessage()
	{
		return message;
	}

	public String getRawErrorReturn()
	{
		return rawErrorReturn;
	}

	public T getValue()
	{
		return value;
	}


	public String getShortErrorMessage()
	{
		String messageWhole = message;

		if(rawErrorReturn != null)
			messageWhole = rawErrorReturn;

		if(messageWhole != null)
			return messageWhole;
		return "An unknown error occured";
	}

}
