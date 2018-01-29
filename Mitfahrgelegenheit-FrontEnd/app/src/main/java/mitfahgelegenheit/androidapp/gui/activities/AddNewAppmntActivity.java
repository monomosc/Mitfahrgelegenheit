package mitfahgelegenheit.androidapp.gui.activities;

import android.app.DialogFragment;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.EditText;
import android.widget.SeekBar;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.DatePickerFragment;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.gui.TimePickerFragment;
import mitfahgelegenheit.androidapp.model.appointment.Appointment;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.appointment.RepeatType;
import mitfahgelegenheit.androidapp.rest.action.appointment.CreateAppointment;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

public class AddNewAppmntActivity extends AppCompatActivity
{
	// DATA
	private LocalDataContainer dataContainer;
	private static DateContainer datetimeContainer;

	// UI
	private EditText fromET, toET, kmDrivenET;
	private SeekBar repeatSB;
	private static Button timePicker, datePicker;

	// TASK
	private CreateAppointmentTask createAppointmentTask;


	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_add_new_appmnt);

		datetimeContainer = new DateContainer();

		fromET = findViewById(id.editStartLocation);
		toET = findViewById(id.editTargetLocation);
		repeatSB = findViewById(id.editRepeatSeekbar);
		kmDrivenET = findViewById(id.editKmDriven);

		Button create = findViewById(id.addNewButton);
		create.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				createAppointmentAttempt();
			}
		});

		timePicker = findViewById(id.timePickButton);
		timePicker.setText(datetimeContainer.getTimeString());
		timePicker.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				showTimePickerDialog();
			}
		});

		datePicker = findViewById(id.datePickButton);
		datePicker.setText(datetimeContainer.getDateString());
		datePicker.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				showDatePickerDialog();
			}
		});

		dataContainer = AppointmentViewActivity.getDataContainer();
	}

	public static DateContainer getDateContainer()
	{
		return datetimeContainer;
	}

	private void showDatePickerDialog()
	{
		DialogFragment newFragment = new DatePickerFragment();
		newFragment.show(getFragmentManager(), "datePicker");
	}

	private void showTimePickerDialog()
	{
		DialogFragment newFragment = new TimePickerFragment();
		newFragment.show(getFragmentManager(), "timePicker");
	}

	private boolean isStartValid(String start)
	{
		return !start.isEmpty();
	}

	private boolean isTargetValid(String target)
	{
		return !target.isEmpty();
	}

	private boolean isDateTimeValid(Date date)
	{
		Calendar calendar = Calendar.getInstance();
		calendar.add(Calendar.HOUR_OF_DAY, 1);
		Date min = calendar.getTime();
		if(date.after(min))
		{
			return true;
		}
		else
		{
			return false;
		}
	}

	private boolean isKmValid(String km)
	{
		try
		{
			int kmD = Integer.parseInt(km);
			if(kmD < 0)
				return false;
		}
		catch(NumberFormatException ignored)
		{
			return false;
		}

		return true;
	}

	private void createAppointmentAttempt()
	{
		//resetting errors
		fromET.setError(null);
		toET.setError(null);
		kmDrivenET.setError(null);

		boolean cancel = false;
		View focusView = null;
		String start, target, date, time, kmDriven;
		start = fromET.getText().toString();
		target = toET.getText().toString();
		date = datePicker.getText().toString();
		time = timePicker.getText().toString();
		kmDriven = kmDrivenET.getText().toString();
		Date datetime = datetimeContainer.getDate();

		//0=never 1=daily 2=weekly
		int repeatTypeSliderSetting = repeatSB.getProgress();
		RepeatType repeatType;
		if(repeatTypeSliderSetting == 1)
			repeatType = RepeatType.DAILY;
		else
			repeatType = (repeatTypeSliderSetting == 0) ? RepeatType.NONE : RepeatType.WEEKLY;

		if(!isStartValid(start))
		{
			fromET.setError("this start location is invalid/too short");
			focusView = fromET;
			cancel = true;
		}
		if(!isTargetValid(target))
		{
			toET.setError("this target lovation is invalid/too short");
			focusView = toET;
			cancel = true;
		}
		if(!isKmValid(kmDriven))
		{
			kmDrivenET.setError("this distance is invalid!");
			focusView = kmDrivenET;
			cancel = true;
		}
		if(!isDateTimeValid(datetime))
		{
			timePicker.setError("");
			datePicker.setError("");
			focusView = datePicker;
			cancel = true;
			new SimpleDialogue("Cannot create appointment", "A new appointment must be at least one hour in the future!").show();
		}


		if(cancel)
			focusView.requestFocus();
		else
		{
			if(createAppointmentTask != null)
				return;

			Appointment appointment = new Appointment(-1, start, target, datetime.getTime()/1000, repeatType, null);
			appointment.addKmDistance(Integer.parseInt(kmDriven));
			createAppointmentTask = new CreateAppointmentTask(appointment);
			createAppointmentTask.execute((Void) null);
		}
	}


	public class CreateAppointmentTask extends AsyncTask<Void, Void, Void>
	{

		private final Appointment appointment;


		// INIT
		public CreateAppointmentTask(Appointment appointment)
		{
			this.appointment = appointment;
		}


		// TASK
		@Override protected Void doInBackground(Void... params)
		{
			UserSettings userSettings = UserSettings.load(AddNewAppmntActivity.this);
			CreateAppointment createAppointment = new CreateAppointment(userSettings.getRestUrl(),
					userSettings.getAuthToken(),
					appointment);


			Runnable onSuccessClose = new Runnable()
			{
				@Override public void run()
				{
					finish();
				}
			};

			ActionResult<Void> result = createAppointment.execute();
			if(result.isSuccess())
				new SimpleDialogue("Creating appointment", "Creation successful!")
						.setOnClose(onSuccessClose)
						.show();
			else
				new SimpleDialogue("Error on appointment creation",
						result.getShortErrorMessage()).show();

			return null;
		}

		@Override protected void onPostExecute(Void ignored)
		{
			AppointmentViewActivity.data.updateAsync();
			createAppointmentTask = null;
		}

		@Override protected void onCancelled()
		{
			createAppointmentTask = null;
		}

	}

	public static class DateContainer
	{
		private final Calendar calendar = Calendar.getInstance();
		Date date;
		SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.ENGLISH);
		SimpleDateFormat dateFormat = new SimpleDateFormat("dd.MM.yyyy", Locale.ENGLISH);

		public DateContainer()
		{
			calendar.add(Calendar.HOUR_OF_DAY, 1);
			date = calendar.getTime();
		}

		public String getTimeString()
		{
			return timeFormat.format(date);
		}

		public String getDateString()
		{
			return dateFormat.format(date);
		}

		public void changeDate(Date date)
		{
			this.date = date;
			timePicker.setText(getTimeString());
			datePicker.setText(getDateString());
		}

		public Date getDate()
		{
			return date;
		}
	}

}
