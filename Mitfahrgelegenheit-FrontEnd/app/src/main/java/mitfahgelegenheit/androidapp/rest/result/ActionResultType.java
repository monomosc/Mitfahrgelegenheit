package mitfahgelegenheit.androidapp.rest.result;

public enum ActionResultType
{

	SUCCESS,
	FAILURE;


	public <T> ActionResult<T> withMessage(String message, String rawReturn)
	{
		return new ActionResult<>(this, message, rawReturn, null);
	}

	public <T> ActionResult<T> withValue(T value)
	{
		return new ActionResult<>(this, null, null, value);
	}

}
