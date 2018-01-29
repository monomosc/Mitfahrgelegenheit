package mitfahgelegenheit.androidapp.gui.activities;

import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.ListView;
import mitfahgelegenheit.androidapp.R;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.gui.adapter.ArchiveListViewAdapter;
import mitfahgelegenheit.androidapp.rest.action.appointment.RetireAppointment;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;

import java.util.ArrayList;
import java.util.List;

public class ArchiveActivity extends AppCompatActivity
{

	private SendArchiveTask sendArchiveTask;


	// INIT
	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_archive);
		final int appointmentId = getIntent().getExtras().getInt("appointmentId");

		ListView listView = findViewById(R.id.archiveUsersListView);
		final ArchiveListViewAdapter adapter = new ArchiveListViewAdapter(this, appointmentId);
		listView.setAdapter(adapter);

		Button confirm = findViewById(R.id.archiveConfirmButton);
		confirm.setOnClickListener(new View.OnClickListener()
		{
			@Override public void onClick(View v)
			{
				confirm(appointmentId, adapter);
			}
		});
	}

	private void confirm(int appointmentId, ArchiveListViewAdapter adapter)
	{
		List<CheckBox> boxes = adapter.getBoxes();
		List<Integer> participatingUsers = new ArrayList<>();
		for(int i = 0; i < boxes.size(); i++)
			if(boxes.get(i).isChecked())
				participatingUsers.add(adapter.getParticipations().get(i).getUserId());

		if(sendArchiveTask != null)
			return;

		sendArchiveTask = new SendArchiveTask(appointmentId, participatingUsers);
		sendArchiveTask.execute((Void) null);
	}


	// TASK
	public class SendArchiveTask extends AsyncTask<Void, Void, Void>
	{

		private final int appointmentId;
		private final List<Integer> driverUserIds;


		// INIT
		public SendArchiveTask(int appointmentId, List<Integer> driverUserIds)
		{
			this.appointmentId = appointmentId;
			this.driverUserIds = driverUserIds;
		}


		// TASK
		@Override protected Void doInBackground(Void... params)
		{
			RetireAppointment retireAppointment = new RetireAppointment(
					UserSettings.load(ArchiveActivity.this).getRestUrl(),
					UserSettings.load(ArchiveActivity.this).getAuthToken(),
					appointmentId,
					driverUserIds);

			Runnable onSuccessClose = new Runnable()
			{
				@Override public void run()
				{
					finish();
				}
			};

			ActionResult<Void> result = retireAppointment.execute();
			if(result.isSuccess())
				new SimpleDialogue("Archiving appointment", "Archiving successful!")
						.setOnClose(onSuccessClose)
						.show();
			else
				new SimpleDialogue("Error on archiving appointment", result.getShortErrorMessage()).show();

			return null;
		}

		@Override protected void onPostExecute(Void ignored)
		{
			AppointmentViewActivity.getDataContainer().updateAsync();
			sendArchiveTask = null;
		}

		@Override protected void onCancelled()
		{
			sendArchiveTask = null;
		}

	}

}
