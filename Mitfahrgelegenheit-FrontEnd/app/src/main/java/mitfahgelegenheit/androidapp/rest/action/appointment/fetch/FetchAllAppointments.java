package mitfahgelegenheit.androidapp.rest.action.appointment.fetch;

import com.google.gson.reflect.TypeToken;
import mitfahgelegenheit.androidapp.model.appointment.Appointment;
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

public class FetchAllAppointments extends RestAction<List<Appointment>>
{

	// INIT
	public FetchAllAppointments(AbstractURL restUrl, String authToken)
	{
		super(restUrl, authToken);
	}


	// ACTION
	@Override public ActionResult<List<Appointment>> execute()
	{
		AbstractURL usersUrl = new AbstractURL(restUrl, "/appointments?finished=true");
		MattpRequest request = new MattpRequest(usersUrl, MattpMethod.GET);

		TypeFromStringDeserializer<List<Appointment>> serializer = new TypeFromStringDeserializer(new TypeToken<ArrayList<Appointment>>() {});
		MattpRequestEnvoy<List<Appointment>> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(serializer));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<List<Appointment>> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(response.getContent().get());
	}

}
