package mitfahgelegenheit.androidapp.gui.activities;

import android.content.Context;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.ListView;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.gui.adapter.ParticipationListViewAdapter;

public class OwnParticipationsViewActivity extends AppCompatActivity
{

	private ListView listView;
	private ParticipationListViewAdapter adapter;
	private Context context;
	private boolean isTimeSorted = false;
	private boolean isStatusSorted = false;
	private boolean isDrivingLevelSorted = false;

	// INIT
	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_own_participations_view);
		Toolbar toolbar = findViewById(id.toolbarPW);
		setSupportActionBar(toolbar);
		context = this;

		listView = findViewById(id.listViewPV);
		adapter = new ParticipationListViewAdapter(context);
		listView.setAdapter(adapter);

		Button sortByTime = findViewById(id.sortPtimeButton);
		sortByTime.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				adapter.sortByTime(isTimeSorted);
				isTimeSorted = !isTimeSorted;
				isStatusSorted = false;
				isDrivingLevelSorted = false;
			}
		});

		Button sortByStatus = findViewById(id.sortPstatusButton);
		sortByStatus.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				adapter.sortByStatus(isStatusSorted);
				isTimeSorted = false;
				isStatusSorted = !isStatusSorted;
				isDrivingLevelSorted = false;
			}
		});

		Button sortBycarLvl = findViewById(id.sortPcarLvlButton);
		sortBycarLvl.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				adapter.sortByDrivingLevel(isDrivingLevelSorted);
				isTimeSorted = false;
				isStatusSorted = false;
				isDrivingLevelSorted = !isDrivingLevelSorted;
			}
		});


		AppointmentViewActivity.getDataContainer().registerRunOnUpdateTask(new Runnable()
		{
			@Override public void run()
			{
				adapter.updateParticipations();
			}
		});
	}

}
