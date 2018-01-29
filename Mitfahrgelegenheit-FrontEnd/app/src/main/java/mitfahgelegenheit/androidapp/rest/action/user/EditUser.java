package mitfahgelegenheit.androidapp.rest.action.user;

import mitfahgelegenheit.androidapp.model.user.UserWithPassword;
import mitfahgelegenheit.androidapp.rest.action.RestAction;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.mattp.MattpRequestEnvoy;
import mitfahgelegenheit.androidapp.rest.mattp.authproviders.TokenAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpMethod;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import mitfahgelegenheit.androidapp.rest.mattp.request.bodies.MattpJsonBody;
import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.readers.MattpSerializedObjectReader;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.rest.result.ActionResultType;
import mitfahgelegenheit.androidapp.rest.result.MessageWrapper;
import mitfahgelegenheit.androidapp.rest.serialization.tostring.BasicFromStringDeserializer;
import mitfahgelegenheit.androidapp.rest.serialization.GsonUtil;

public class EditUser extends RestAction<Void>
{

	private final UserWithPassword userWithPassword;


	// INIT
	public EditUser(AbstractURL restUrl, String authToken, UserWithPassword userWithPassword)
	{
		super(restUrl, authToken);
		this.userWithPassword = userWithPassword;
	}


	// ACTION
	@Override public ActionResult<Void> execute()
	{
		String userWithPasswordSerialized = GsonUtil.get().toJson(userWithPassword);

		AbstractURL usersUrl = new AbstractURL(restUrl, "/users/"+userWithPassword.getId());
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.PUT);
		request.setBody(new MattpJsonBody(userWithPasswordSerialized));

		MattpRequestEnvoy<MessageWrapper> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(MessageWrapper.class)));
		envoy.setAuthProvider(new TokenAuthProvider(authToken));

		RequestResponse<MessageWrapper> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(null);
	}

}
