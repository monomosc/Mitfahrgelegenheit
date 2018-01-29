package mitfahgelegenheit.androidapp.gui.activities;

import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.widget.ListView;
import mitfahgelegenheit.androidapp.R;
import mitfahgelegenheit.androidapp.gui.adapter.UserListViewAdapter;

public class ParticipatingUsersViewActivity extends AppCompatActivity
{

	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_participating_users_view);

		int appointmentId = getIntent().getExtras().getInt("appointmentId");

		ListView listView = findViewById(R.id.participatingUsersListView);
		final UserListViewAdapter adapter = new UserListViewAdapter(this, appointmentId);
		listView.setAdapter(adapter);

		AppointmentViewActivity.getDataContainer().registerRunOnUpdateTask(new Runnable()
		{
			@Override public void run()
			{
				adapter.update();
			}
		});
	}

}
