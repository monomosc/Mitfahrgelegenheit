package mitfahgelegenheit.androidapp.gui.activities;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.ListView;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.adapter.AppointmentListViewAdapter;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;

public class AppointmentViewActivity extends AppCompatActivity
{

	private android.content.Context context;
	public static LocalDataContainer data = null;
	public AppointmentListViewAdapter adapter;

	private boolean isTimeAscSorted = false;
	private boolean isStartAscSorted = false;
	private boolean isTargetAscSorted = false;
	private boolean isRepeatAscSorted = false;
	private boolean isCycleAscSorted = false;


	// UPDATE
	@Override protected void onResume()
	{
		super.onResume();
		data.updateAsync();
	}


	// INIT
	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		context = this;

		data = new LocalDataContainer(this);
		data.registerRunOnUpdateTask(new Runnable()
		{
			@Override public void run()
			{
				update();
			}
		});

		setContentView(layout.activity_appointment_view);
		Toolbar toolbar = findViewById(id.toolbar);
		setSupportActionBar(toolbar);

		//ListView for the appointments. Adapter loads the Strings via TextViews into the ListView
		ListView listView = findViewById(id.listView);
		adapter = new AppointmentListViewAdapter(context);
		listView.setAdapter(adapter);


		Button sortByTimeButton = findViewById(id.SortByTimeButton);
		sortByTimeButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				sortByTime();
			}
		});

		Button sortByStartButton = findViewById(id.SortByStartButton);
		sortByStartButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				sortByStart();
			}
		});

		Button sortByTargetButton = findViewById(id.SortByTargetButton);
		sortByTargetButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				sortByTarget();
			}
		});

		Button sortByDriverButton = findViewById(id.SortByRepeatType);
		sortByDriverButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				sortByRepeat();
			}
		});

		Button sortByLifeCylceButton = findViewById(id.SortByLifeCycle);
		sortByLifeCylceButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				sortByStatus();
			}
		});

		Button editUserData = findViewById(id.userOptionButton);
		editUserData.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				startUserDataActivity();
			}
		});

		Button addNewAppmnt = findViewById(id.newAppointmentButton);
		addNewAppmnt.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				startAddNewAppmntActivity();
			}
		});

		Button yourParticipations = findViewById(id.yourParticipationButton);
		yourParticipations.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				startOwnParticipationsViewActivity();
			}
		});

		Button logOut = findViewById(id.logOutButton);
		logOut.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				logout();
			}
		});

		Button upDate = findViewById(id.updateButton);
		upDate.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				data.updateAsync();
			}
		});
	}


	private void sortByTime()
	{
		data.sortByStartTime(isTimeAscSorted);
		isTimeAscSorted = !isTimeAscSorted;
		isStartAscSorted = false;
		isTargetAscSorted = false;
		isRepeatAscSorted = false;
		isCycleAscSorted = false;
		update();
	}

	private void sortByStart()
	{
		data.sortByStart(isStartAscSorted);
		isTimeAscSorted = false;
		isStartAscSorted = !isStartAscSorted;
		isTargetAscSorted = false;
		isRepeatAscSorted = false;
		isCycleAscSorted = false;
		update();
	}

	private void sortByTarget()
	{
		data.sortByTarget(isTargetAscSorted);
		isTimeAscSorted = false;
		isStartAscSorted = false;
		isTargetAscSorted = !isTargetAscSorted;
		isRepeatAscSorted = false;
		isCycleAscSorted = false;
		update();
	}

	private void sortByRepeat()
	{
		data.sortByRepeatType(isRepeatAscSorted);
		isTimeAscSorted = false;
		isStartAscSorted = false;
		isTargetAscSorted = false;
		isRepeatAscSorted = !isRepeatAscSorted;
		isCycleAscSorted = false;
		update();
	}

	private void sortByStatus()
	{
		data.sortByLifeCycle(isCycleAscSorted);
		isTimeAscSorted = false;
		isStartAscSorted = false;
		isTargetAscSorted = false;
		isRepeatAscSorted = false;
		isCycleAscSorted = !isCycleAscSorted;
		update();
	}

	private void logout()
	{
		UserSettings.load(this).setAuthToken("");
		data.clear();

		startActivity(new Intent(context, LoginActivity.class));
		finish();
	}

	private void startOwnParticipationsViewActivity()
	{
		Intent intent = new Intent(context, OwnParticipationsViewActivity.class);
		startActivity(intent);
	}

	private void startAddNewAppmntActivity()
	{
		Intent intent = new Intent(context, AddNewAppmntActivity.class);
		startActivity(intent);
	}


	private void startUserDataActivity()
	{
		Intent intent = new Intent(context, UserDataEditActivity.class);
		startActivity(intent);
	}

	public void update()
	{
		adapter.notifyDataSetChanged();
	}


	//GET STATICS
	public static LocalDataContainer getDataContainer() {return data;}

}
