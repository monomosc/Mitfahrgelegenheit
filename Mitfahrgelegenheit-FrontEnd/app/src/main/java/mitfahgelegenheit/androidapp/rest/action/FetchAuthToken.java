package mitfahgelegenheit.androidapp.rest.action;

import com.google.gson.annotations.SerializedName;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.mattp.MattpRequestEnvoy;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpMethod;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import mitfahgelegenheit.androidapp.rest.mattp.request.bodies.MattpJsonBody;
import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.readers.MattpSerializedObjectReader;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.rest.result.ActionResultType;
import mitfahgelegenheit.androidapp.rest.serialization.tostring.BasicFromStringDeserializer;
import mitfahgelegenheit.androidapp.rest.serialization.GsonUtil;
import mitfahgelegenheit.androidapp.rest.serialization.ByDeserialization;

public class FetchAuthToken extends RestAction<String>
{

	private final String username;
	private final String password;


	// INIT
	public FetchAuthToken(AbstractURL restUrl, String username, String password)
	{
		super(restUrl, null);

		this.username = username;
		this.password = password;
	}


	@Override public ActionResult<String> execute()
	{
		RequestObject requestObject = new RequestObject(username, password);
		String requestObjectSerialized = GsonUtil.get().toJson(requestObject);

		AbstractURL authUrl = new AbstractURL(restUrl, "/auth");
		MattpRequest request = new MattpRequest(authUrl, MattpMethod.POST);
		request.setBody(new MattpJsonBody(requestObjectSerialized));

		MattpRequestEnvoy<ResponseObject> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(ResponseObject.class)));

		RequestResponse<ResponseObject> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(response.getContent().get().accessToken);
	}


	private static final class RequestObject
	{

		@ByDeserialization private final String username;
		@ByDeserialization private final String password;


		// INIT
		private RequestObject(String username, String password)
		{
			this.username = username;
			this.password = password;
		}

	}

	private static final class ResponseObject
	{

		@SerializedName("access_token") private final String accessToken;

		// INIT
		private ResponseObject(String accessToken)
		{
			this.accessToken = accessToken;
		}

	}

}
