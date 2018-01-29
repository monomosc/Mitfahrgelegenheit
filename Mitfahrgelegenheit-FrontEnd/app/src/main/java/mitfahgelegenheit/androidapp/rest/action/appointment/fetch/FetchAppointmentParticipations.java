package mitfahgelegenheit.androidapp.rest.action.appointment.fetch;

import com.google.gson.reflect.TypeToken;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
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

public class FetchAppointmentParticipations extends RestAction<List<Participation>>
{

	private final int appointmentId;


	public FetchAppointmentParticipations(AbstractURL restUrl, String authToken, int appointmentId)
	{
		super(restUrl, authToken);
		this.appointmentId = appointmentId;
	}


	@Override public ActionResult<List<Participation>> execute()
	{
		AbstractURL url = new AbstractURL(restUrl, "/appointments/"+appointmentId+"/users");
		MattpRequest request = new MattpRequest(url, MattpMethod.GET);

		TypeFromStringDeserializer<List<Participation>> serializer = new TypeFromStringDeserializer(new TypeToken<ArrayList<Participation>>() {});
		MattpRequestEnvoy<List<Participation>> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(serializer));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<List<Participation>> response = envoy.send();

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());


		List<Participation> participations = response.getContent().get();

		List<Participation> appointmentParticipationsWithId = new ArrayList<>();
		for(Participation p : participations)
			appointmentParticipationsWithId.add(new Participation(p.getUserId(),
					appointmentId,
					p.getParticipationType(),
					p.getMaximumPassengers()));

		return ActionResultType.SUCCESS.withValue(appointmentParticipationsWithId);
	}

}
