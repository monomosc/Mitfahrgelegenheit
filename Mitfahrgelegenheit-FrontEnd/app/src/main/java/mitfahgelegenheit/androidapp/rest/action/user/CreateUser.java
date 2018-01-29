package mitfahgelegenheit.androidapp.rest.action.user;

import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.model.user.UserWithPassword;
import mitfahgelegenheit.androidapp.rest.action.RestAction;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.mattp.MattpRequestEnvoy;
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

public class CreateUser extends RestAction<Void>
{

	private final User user;
	private final String password;


	// INIT
	public CreateUser(AbstractURL restUrl, User user, String password)
	{
		super(restUrl, null);

		this.user = user;
		this.password = password;
	}


	// ACTION
	@Override public ActionResult<Void> execute()
	{
		UserWithPassword requestObject = new UserWithPassword(user, password);
		String requestObjectSerialized = GsonUtil.get().toJson(requestObject);

		AbstractURL usersUrl = new AbstractURL(restUrl, "/users");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.POST);
		request.setBody(new MattpJsonBody(requestObjectSerialized));

		MattpRequestEnvoy<MessageWrapper> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(MessageWrapper.class)));

		RequestResponse<MessageWrapper> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(null);
	}

}
