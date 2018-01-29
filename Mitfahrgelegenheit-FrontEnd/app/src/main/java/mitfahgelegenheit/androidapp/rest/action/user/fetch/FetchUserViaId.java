package mitfahgelegenheit.androidapp.rest.action.user.fetch;

import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.rest.action.RestAction;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.mattp.MattpRequestEnvoy;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpMethod;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.readers.MattpSerializedObjectReader;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.rest.result.ActionResultType;
import mitfahgelegenheit.androidapp.rest.serialization.tostring.BasicFromStringDeserializer;

public class FetchUserViaId extends RestAction<User>
{

	private final int userId;


	public FetchUserViaId(AbstractURL restUrl, String authToken, int userId)
	{
		super(restUrl, authToken);

		this.userId = userId;
	}


	@Override public ActionResult<User> execute()
	{
		AbstractURL usersUrl = new AbstractURL(restUrl, "/users/"+userId);
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.GET);

		MattpRequestEnvoy<User> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(User.class)));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<User> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(response.getContent().get());
	}

}
