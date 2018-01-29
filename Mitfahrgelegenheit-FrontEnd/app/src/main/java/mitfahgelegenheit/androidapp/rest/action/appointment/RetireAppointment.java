package mitfahgelegenheit.androidapp.rest.action.appointment;

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

import java.util.List;

public class RetireAppointment extends RestAction<Void>
{

	private final int appointmentId;
	private final List<Integer> driverUserIds;


	public RetireAppointment(AbstractURL restUrl, String authToken, int appointmentId, List<Integer> driverUserIds)
	{
		super(restUrl, authToken);

		this.appointmentId = appointmentId;
		this.driverUserIds = driverUserIds;
	}


	public ActionResult<Void> execute()
	{
		String driversSerialized = GsonUtil.get().toJson(new SendObject(driverUserIds));

		AbstractURL usersUrl = new AbstractURL(restUrl, "/appointments/"+appointmentId+"/retire");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.POST);
		request.setBody(new MattpJsonBody(driversSerialized));

		MattpRequestEnvoy<MessageWrapper> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(MessageWrapper.class)));
		envoy.setAuthProvider(new TokenAuthProvider(authToken));

		RequestResponse<MessageWrapper> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(null);
	}


	private static class SendObject
	{

		private final List<Integer> drivers;

		// INIT
		private SendObject(List<Integer> drivers)
		{
			this.drivers = drivers;
		}

	}

}
