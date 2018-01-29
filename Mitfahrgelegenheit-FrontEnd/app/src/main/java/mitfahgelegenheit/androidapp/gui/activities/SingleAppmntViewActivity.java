package mitfahgelegenheit.androidapp.gui.activities;

import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.EditText;
import android.widget.SeekBar;
import android.widget.TextView;
import mitfahgelegenheit.androidapp.R;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.model.appointment.Appointment;
import mitfahgelegenheit.androidapp.model.appointment.AppointmentStatus;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
import mitfahgelegenheit.androidapp.model.appointment.Participation.ParticipationType;
import mitfahgelegenheit.androidapp.rest.action.appointment.ParticipateInAppointment;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.util.MyOptional;

public class SingleAppmntViewActivity extends AppCompatActivity
{

	// UI
	private SeekBar willDriveSB;
	private EditText freeSeatsET;

	// DATA
	private Appointment appointment;

	// TASK
	private ParticipateTask participateTask;


	// INIT
	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_single_appmnt_view);

		int appointmentId = getIntent().getExtras().getInt("appointmentId");
		displayAppointment(appointmentId);

		AppointmentViewActivity.getDataContainer().registerRunOnUpdateTask(new Runnable()
		{
			@Override public void run()
			{
				displayAppointment(getIntent().getExtras().getInt("appointmentId"));
			}
		});
	}

	private void displayAppointment(final int appointmentId)
	{
		LocalDataContainer dataContainer = AppointmentViewActivity.getDataContainer();
		appointment = dataContainer.getAppointmentById(appointmentId);

		TextView startLocation = findViewById(R.id.textSingleStartLocation);
		startLocation.setText(appointment.getStartLocation());

		TextView targetLocation = findViewById(R.id.textSingleTargetLocation);
		targetLocation.setText(appointment.getTargetLocation());

		TextView datetime = findViewById(R.id.textSingleDateTime);
		datetime.setText(appointment.timeToString());

		TextView repeatType = findViewById(R.id.textSingleRepeatType);
		repeatType.setText(appointment.getRepeatType().toString());

		TextView distance = findViewById(R.id.textKmView);
		distance.setText(""+appointment.getKmdistance()+" km");

		willDriveSB = findViewById(R.id.carAvailabilitySeekBar);

		freeSeatsET = findViewById(R.id.editFreeSeats);

		Button participate = findViewById(R.id.participationButton);
		participate.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				participationAttempt();
			}
		});

		Participation participation = dataContainer.getParticipation(dataContainer.getCurrentUser().getId(), appointmentId);
		if(participation != null)
		{

			willDriveSB.setProgress(participation.getParticipationType().intValue);
			freeSeatsET.setText(Integer.toString(participation.getMaximumPassengers()));
		}

		Button userListButton = findViewById(R.id.participationgUsersButton);
		userListButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				showUsers(appointmentId);
			}
		});

		Button archiveButton = findViewById(R.id.achiveAppointmentButton);
		archiveButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				archiveAppointment(appointment.getStatus(), appointmentId);
			}
		});
	}

	private void archiveAppointment(AppointmentStatus status, int appointmentId)
	{
		switch(status)
		{
			case UNFINISHED:
				new SimpleDialogue("Can't archive appointment", "Appointment is still open").show();
				break;
			case LOCKED_FIT_DEFINITE:
			case LOCKED_FIT_POSSIBLE:
			case LOCKED_NO_FIT:
				archive(appointmentId);
				break;
			case RETIRED:
				new SimpleDialogue("Can't archive appointment", "Appointment is already archived").show();
				break;
			case BROKEN:
				new SimpleDialogue("Can't archive appointment", "Appointment is broken").show();
				break;
		}
	}

	private void archive(int appointmentId)
	{
		Intent intent = new Intent(this, ArchiveActivity.class);
		intent.putExtra("appointmentId", appointmentId);
		startActivity(intent);
	}

	private void showUsers(int appointmentId)
	{
		Intent intent = new Intent(this, ParticipatingUsersViewActivity.class);
		intent.putExtra("appointmentId", appointmentId);
		startActivity(intent);
	}

	// READ DATA
	@NonNull private MyOptional<Participation> getParticipationIfValid()
	{
		//reset error
		freeSeatsET.setError(null);


		//0=noCar 1=willDrive 2=mayDrive
		int willDrive = willDriveSB.getProgress();

		int seats;
		try
		{
			seats = Integer.parseInt(freeSeatsET.getText().toString());
		}
		catch(NumberFormatException ignored)
		{
			freeSeatsET.setError("Invalid number of seats");
			freeSeatsET.requestFocus();
			return MyOptional.empty();
		}

		if(seats < 0)
		{
			freeSeatsET.setError("number of free seats is invalid");
			freeSeatsET.requestFocus();
			return MyOptional.empty();
		}

		if((willDrive != 0) && (seats == 0))
		{
			freeSeatsET.setError("At least 1 seat needed for driving");
			freeSeatsET.requestFocus();
			return MyOptional.empty();
		}

		if((willDrive == 0) && (seats > 0))
		{
			freeSeatsET.setError("Has to be zero when not driving");
			freeSeatsET.requestFocus();
			return MyOptional.empty();
		}

		int userId = AppointmentViewActivity.getDataContainer().getCurrentUser().getId();
		ParticipationType participationType = ParticipationType.fromIntValue(willDrive);

		return MyOptional.of(new Participation(userId, appointment.getId(), participationType, seats));
	}


	// PARTICIPATE
	private void participationAttempt()
	{
		MyOptional<Participation> participationOptional = getParticipationIfValid();
		if(!participationOptional.isPresent())
			return;

		if(participateTask != null)
			return;

		Participation participation = participationOptional.get();
		participateTask = new ParticipateTask(participation);
		participateTask.execute((Void) null);
	}


	// TASK
	public class ParticipateTask extends AsyncTask<Void, Void, Void>
	{

		private final Participation participation;


		// INIT
		public ParticipateTask(Participation participation)
		{
			this.participation = participation;
		}


		// TASK
		@Override protected Void doInBackground(Void... params)
		{
			UserSettings userSettings = UserSettings.load(SingleAppmntViewActivity.this);
			ParticipateInAppointment participateInAppointment = new ParticipateInAppointment(userSettings.getRestUrl(),
					userSettings.getAuthToken(),
					participation);

			ActionResult<Void> result = participateInAppointment.execute();
			if(result.isSuccess())
				new SimpleDialogue("Appointment participation", "Participation in appointment successful!").show();
			else
				new SimpleDialogue("Error on participating", result.getShortErrorMessage()).show();

			return null;
		}

		@Override protected void onPostExecute(Void ignored)
		{
			AppointmentViewActivity.getDataContainer().updateAsync();
			participateTask = null;
		}

		@Override protected void onCancelled()
		{
			participateTask = null;
		}

	}

}
