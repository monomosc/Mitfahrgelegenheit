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

public class FetchUserDistance extends RestAction<Integer>
{

	private final int userId;


	public FetchUserDistance(AbstractURL restUrl, String authToken, int userId)
	{
		super(restUrl, authToken);
		this.userId = userId;
	}


	@Override public ActionResult<Integer> execute()
	{
		AbstractURL usersUrl = new AbstractURL(restUrl, "/users/"+userId+"/distance");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.GET);

		MattpRequestEnvoy<ReturnObject> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(ReturnObject.class)));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<ReturnObject> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		int distance = response.getContent().get().distance;
		return ActionResultType.SUCCESS.withValue(distance);
	}


	private static class ReturnObject
	{

		@ByDeserialization private int distance;

	}

}
