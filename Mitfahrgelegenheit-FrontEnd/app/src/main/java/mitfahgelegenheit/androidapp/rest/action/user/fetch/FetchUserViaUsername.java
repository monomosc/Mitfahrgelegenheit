package mitfahgelegenheit.androidapp.rest.action.user.fetch;

import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.rest.action.RestAction;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.rest.result.ActionResultType;

public class FetchUserViaUsername extends RestAction<User>
{

	private final String username;


	public FetchUserViaUsername(AbstractURL restUrl, String authToken, String username)
	{
		super(restUrl, authToken);
		this.username = username;
	}


	@Override public ActionResult<User> execute()
	{
		FetchUserId fetchUserId = new FetchUserId(restUrl, authToken, username);
		ActionResult<Integer> fetchIdResult = fetchUserId.execute();
		if(!fetchIdResult.isSuccess())
			return ActionResultType.FAILURE.withMessage(fetchIdResult.getMessage(), fetchIdResult.getRawErrorReturn());

		int userId = fetchIdResult.getValue();
		FetchUserViaId fetchUserViaId = new FetchUserViaId(restUrl, authToken, userId);

		return fetchUserViaId.execute();
	}

}
