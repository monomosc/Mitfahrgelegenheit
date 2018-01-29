package mitfahgelegenheit.androidapp.rest.action.user.fetch;

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
import mitfahgelegenheit.androidapp.rest.serialization.ByDeserialization;

public class FetchUserId extends RestAction<Integer>
{

	private final String username;


	public FetchUserId(AbstractURL restUrl, String authToken, String username)
	{
		super(restUrl, authToken);

		this.username = username;
	}


	@Override public ActionResult<Integer> execute()
	{
		AbstractURL usersUrl = new AbstractURL(restUrl, "/users/"+username);
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.GET);

		MattpRequestEnvoy<ReturnObject> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(ReturnObject.class)));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<ReturnObject> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		int userId = response.getContent().get().id;
		return ActionResultType.SUCCESS.withValue(userId);
	}


	private static class ReturnObject
	{

		@ByDeserialization private int id;

	}

}
