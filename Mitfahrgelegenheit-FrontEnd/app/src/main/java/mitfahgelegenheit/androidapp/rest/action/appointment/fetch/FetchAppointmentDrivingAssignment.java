package mitfahgelegenheit.androidapp.rest.action.appointment.fetch;

import mitfahgelegenheit.androidapp.model.appointment.DrivingAssignment;
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

public class FetchAppointmentDrivingAssignment extends RestAction<DrivingAssignment>
{

	private final int appointmentId;


	public FetchAppointmentDrivingAssignment(AbstractURL restUrl, String authToken, int appointmentId)
	{
		super(restUrl, authToken);
		this.appointmentId = appointmentId;
	}


	@Override public ActionResult<DrivingAssignment> execute()
	{
		AbstractURL url = new AbstractURL(restUrl, "/appointments/"+appointmentId+"/drivingDistribution");
		MattpRequest request = new MattpRequest(url, MattpMethod.GET);


		MattpRequestEnvoy<DrivingAssignment> envoy = new MattpRequestEnvoy<>(request,
				new MattpSerializedObjectReader<>(new BasicFromStringDeserializer<>(DrivingAssignment.class)));
		envoy.setAuthProvider(getAuthProvider());

		RequestResponse<DrivingAssignment> response = envoy.send();
		System.out.println("drivingAssignment ("+appointmentId+"): "+response);

		if(!response.isSuccess())
			return ActionResultType.FAILURE.withMessage(response.toString(), response.getErrorMessage().get());

		return ActionResultType.SUCCESS.withValue(response.getContent().get());
	}

}
