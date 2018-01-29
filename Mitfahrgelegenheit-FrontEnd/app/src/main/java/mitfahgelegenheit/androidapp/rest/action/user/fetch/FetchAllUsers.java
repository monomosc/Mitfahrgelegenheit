package mitfahgelegenheit.androidapp.rest.action.user.fetch;

import com.google.gson.reflect.TypeToken;
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
import mitfahgelegenheit.androidapp.rest.serialization.tostring.TypeFromStringDeserializer;

import java.util.ArrayList;
import java.util.List;

public class FetchAllUsers extends RestAction<List<User>>
{

	public FetchAllUsers(AbstractURL restUrl, String authToken)
	{
		super(restUrl, authToken);
	}


	@Override public ActionResult<List<User>> execute()
	{
		AbstractURL usersUrl = new AbstractURL(restUrl, "/users");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.GET);

		TypeFromStringDeserializer<List<User>> serializer = new TypeFromStringDeserializer(new TypeToken<ArrayList<User>>() {});
		MattpRequestEnvoy<List<User>> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(serializer));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<List<User>> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(response.getContent().get());
	}

}
