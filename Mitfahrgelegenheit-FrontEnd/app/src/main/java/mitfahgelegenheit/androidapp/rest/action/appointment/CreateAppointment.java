package mitfahgelegenheit.androidapp.rest.action.appointment;

import mitfahgelegenheit.androidapp.model.appointment.Appointment;
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

public class CreateAppointment extends RestAction<Void>
{

	private final Appointment appointment;


	// INIT
	public CreateAppointment(AbstractURL restUrl, String authToken, Appointment appointment)
	{
		super(restUrl, authToken);

		this.appointment = appointment;
	}


	// ACTION
	@Override public ActionResult<Void> execute()
	{
		String appointmentSerialized = GsonUtil.get().toJson(appointment);

		AbstractURL usersUrl = new AbstractURL(restUrl, "/appointments");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.POST);
		request.setBody(new MattpJsonBody(appointmentSerialized));

		MattpRequestEnvoy<MessageWrapper> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(MessageWrapper.class)));
		envoy.setAuthProvider(new TokenAuthProvider(authToken));

		RequestResponse<MessageWrapper> response = envoy.send();
		System.out.println(response);

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(null);
	}

}
