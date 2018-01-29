package mitfahgelegenheit.androidapp.model;

import android.app.Activity;
import android.os.AsyncTask;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.model.appointment.Appointment;
import mitfahgelegenheit.androidapp.model.appointment.AppointmentStatus;
import mitfahgelegenheit.androidapp.model.appointment.DrivingAssignment;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.rest.action.appointment.fetch.FetchAllAppointments;
import mitfahgelegenheit.androidapp.rest.action.appointment.fetch.FetchAppointmentDrivingAssignment;
import mitfahgelegenheit.androidapp.rest.action.appointment.fetch.FetchAppointmentParticipations;
import mitfahgelegenheit.androidapp.rest.action.user.fetch.FetchAllUsers;
import mitfahgelegenheit.androidapp.rest.action.user.fetch.FetchUserDistance;
import mitfahgelegenheit.androidapp.rest.action.user.fetch.FetchUserViaUsername;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.util.AndroidUtil;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Supposed to hold all information that is needed for the application
 * such as users and appointments
 * Is created once in AppointmentViewActivity.
 */
public final class LocalDataContainer
{

	private final UserSettings userSettings;

	// DATA
	private User currentUser;
	private Collection<User> users = new ArrayList<>();
	private Map<Integer, Integer> userDistances = new HashMap<>();

	private List<Appointment> appointments = new ArrayList<>();
	private Collection<Participation> participations = new ArrayList<>();
	private Map<Integer, DrivingAssignment> drivingAssignments = new HashMap<>();

	// UPDATE
	private UpdateDataTask updateDataTask = null;
	private final List<Runnable> runOnUpdateTasks = new ArrayList<>();


	//INIT
	public LocalDataContainer(Activity activityCreatedFrom)
	{
		userSettings = UserSettings.load(activityCreatedFrom);
		updateAsync();
	}

	public void clear()
	{
		if(updateDataTask != null)
			updateDataTask.cancel(true);

		users.clear();
		appointments.clear();
		participations.clear();
		currentUser = null;
	}


	// GETTERS

	public User getCurrentUser() { return currentUser; }

	public Collection<User> getUsers() { return users; }

	public User findUserById(int userId)
	{
		for(User user : users)
			if(user.getId() == userId)
				return user;

		return null;
	}

	public int getUserDistance(int userId)
	{
		return userDistances.get(userId);
	}


	public List<Appointment> getAppointments() { return appointments; }

	public Appointment getAppointmentById(int id)
	{
		for(Appointment appointment : appointments)
			if(appointment.getId() == id)
				return appointment;

		return null;
	}

	public List<List<String>> getAppointmentsToString()
	{
		List<List<String>> strings = new ArrayList<>();

		for(Appointment appointment : appointments)
			strings.add(appointment.toStringArr());

		return strings;
	}


	public List<Participation> getParticipationsOfCurrentUser()
	{
		List<Participation> userParticipations = new ArrayList<>();
		for(Participation participation : participations)
			if(participation.getUserId() == currentUser.getId())
				userParticipations.add(participation);

		return userParticipations;
	}

	public Participation getParticipation(int userId, int appointmentId)
	{
		for(Participation participation : participations)
			if((participation.getUserId() == userId) && (participation.getAppointmentId() == appointmentId))
				return participation;

		return null;
	}

	public List<Participation> getParticipationsForAppointment(int appointmentId)
	{
		ArrayList<Participation> parts = new ArrayList<>();
		for(Participation participation : participations)
		{
			if(participation.getAppointmentId() == appointmentId)
			{
				parts.add(participation);
			}
		}
		return parts;
	}

	public DrivingAssignment getDrivingAssignment(int appointmentId)
	{
		return drivingAssignments.get(appointmentId);
	}


	// SORTING
	public void sortByStart(boolean desc)
	{
		Collections.sort(appointments, new Comparator<Appointment>()
		{
			@Override public int compare(Appointment o1, Appointment o2)
			{
				int temp = o1.getStartLocation().compareTo(o2.getStartLocation());

				if(temp == 0)
					return o1.getStartTimeAsDate().compareTo(o2.getStartTimeAsDate());

				return temp;
			}
		});

		if(desc)
			Collections.reverse(appointments);
	}

	public void sortByTarget(boolean desc)
	{
		Collections.sort(appointments, new Comparator<Appointment>()
		{
			@Override public int compare(Appointment o1, Appointment o2)
			{
				int temp = o1.getTargetLocation().compareTo(o2.getTargetLocation());
				if(temp == 0)
					return o1.getStartTimeAsDate().compareTo(o2.getStartTimeAsDate());

				return temp;
			}
		});

		if(desc)
			Collections.reverse(appointments);
	}

	public void sortByStartTime(boolean desc)
	{
		Collections.sort(appointments, new Comparator<Appointment>()
		{
			@Override public int compare(Appointment o1, Appointment o2)
			{
				return o1.getStartTimeAsDate().compareTo(o2.getStartTimeAsDate());
			}
		});

		if(desc)
			Collections.reverse(appointments);
	}

	public void sortByRepeatType(boolean desc)
	{
		Collections.sort(appointments, new Comparator<Appointment>()
		{
			@Override public int compare(Appointment o1, Appointment o2)
			{
				int temp = o1.getRepeatType().compareTo(o2.getRepeatType());
				if(temp == 0)
					return o1.getStartTimeAsDate().compareTo(o2.getStartTimeAsDate());

				return temp;
			}
		});

		if(desc)
			Collections.reverse(appointments);
	}

	public void sortByLifeCycle(boolean desc)
	{
		final boolean desctmp = desc;
		Collections.sort(appointments, new Comparator<Appointment>()
		{
			@Override public int compare(Appointment o1, Appointment o2)
			{

				int o1_tmp = lifecycleToInt(o1.getStatus(), desctmp);
				int o2_tmp = lifecycleToInt(o2.getStatus(), desctmp);

				if(o1_tmp == o2_tmp)
					return o1.getStartTimeAsDate().compareTo(o2.getStartTimeAsDate());

				return o1_tmp-o2_tmp;
			}
		});

		if(desc)
			Collections.reverse(appointments);
	}

	public int lifecycleToInt(AppointmentStatus cycle, boolean desc)
	{
		int out = 0;
		switch(cycle)
		{
			case UNFINISHED:
				out = 1;
				break;
			case LOCKED_NO_FIT:
			case LOCKED_FIT_DEFINITE:
			case LOCKED_FIT_POSSIBLE:
				out = 2;
				break;
			case RETIRED:
				out = 3;
				break;
			case BROKEN:
				out = 4;
				break;
		}

		if(desc && (out == 4))
			out = 0;

		return out;
	}


	// ONUPDATE
	public void registerRunOnUpdateTask(Runnable runOnUpdateTask)
	{
		runOnUpdateTasks.add(runOnUpdateTask);
	}


	// UPDATE
	public void updateAsync()
	{
		if(updateDataTask != null)
			return;

		updateDataTask = new UpdateDataTask();
		updateDataTask.execute((Void) null);
	}


	private void updateCurrentUser() throws UpdateException
	{
		FetchUserViaUsername fetchUserViaUsername = new FetchUserViaUsername(userSettings.getRestUrl(),
				userSettings.getAuthToken(),
				userSettings.getUsername());
		ActionResult<User> result = fetchUserViaUsername.execute();

		if(result.isSuccess())
			currentUser = result.getValue();
		else
			throw new UpdateException("Error fetching user", result.getShortErrorMessage());
	}

	private void updateUsers() throws UpdateException
	{
		FetchAllUsers fetchAllUsers = new FetchAllUsers(userSettings.getRestUrl(), userSettings.getAuthToken());
		ActionResult<List<User>> result = fetchAllUsers.execute();
		if(result.isSuccess())
			users = new ArrayList<>(result.getValue());
		else
			throw new UpdateException("Error fetching users", result.getShortErrorMessage());
	}

	private void updateUserDrivenDistances() throws UpdateException
	{
		final Map<Integer, Integer> newUserDistance = new HashMap<>();

		ExecutorService threadPoolExecutor = new ThreadPoolExecutor(5,
				5,
				5,
				TimeUnit.MINUTES,
				new LinkedBlockingQueue<Runnable>());
		Collection<Future<?>> futures = new LinkedList<>();

		final String[] error = new String[1];
		for(final User user : users)
		{
			Runnable run = new Runnable()
			{
				@Override public void run()
				{
					FetchUserDistance fetchParticipations = new FetchUserDistance(userSettings.getRestUrl(),
							userSettings.getAuthToken(),
							user.getId());

					ActionResult<Integer> result = fetchParticipations.execute();
					if(result.isSuccess())
						newUserDistance.put(user.getId(), result.getValue());
					else
						error[0] = result.getShortErrorMessage();
				}
			};

			futures.add(threadPoolExecutor.submit(run));
		}

		waitForAllFutures(futures);

		if(error[0] != null)
			throw new UpdateException("Error fetching user distance", error[0]);
		else
			userDistances = newUserDistance;
	}


	private void updateAppointments() throws UpdateException
	{
		FetchAllAppointments fetchAllAppointments = new FetchAllAppointments(userSettings.getRestUrl(),
				userSettings.getAuthToken());
		ActionResult<List<Appointment>> result = fetchAllAppointments.execute();
		if(result.isSuccess())
			appointments = new ArrayList<>(result.getValue());
		else
			throw new UpdateException("Error fetching appointments", result.getShortErrorMessage());
	}

	private void updateParticipations() throws UpdateException
	{
		final Collection<Participation> newParticipations = new ArrayList<>();

		ExecutorService threadPoolExecutor = new ThreadPoolExecutor(5,
				5,
				5,
				TimeUnit.MINUTES,
				new LinkedBlockingQueue<Runnable>());
		Collection<Future<?>> futures = new LinkedList<>();

		final String[] error = new String[1];
		for(final Appointment appointment : appointments)
		{
			Runnable run = new Runnable()
			{
				@Override public void run()
				{
					FetchAppointmentParticipations fetchParticipations = new FetchAppointmentParticipations(userSettings.getRestUrl(),
							userSettings.getAuthToken(),
							appointment.getId());

					ActionResult<List<Participation>> result = fetchParticipations.execute();
					if(result.isSuccess())
						newParticipations.addAll(result.getValue());
					else
						error[0] = result.getShortErrorMessage();
				}
			};

			futures.add(threadPoolExecutor.submit(run));
		}

		waitForAllFutures(futures);

		if(error[0] != null)
			throw new UpdateException("Error fetching appointment participations", error[0]);
		else
			participations = newParticipations;
	}

	private void updateDrivingAssignments() throws UpdateException
	{
		System.out.println("update driving assignments");

		final Map<Integer, DrivingAssignment> newDrivingAssigments = new HashMap<>();

		ExecutorService threadPoolExecutor = new ThreadPoolExecutor(5,
				5,
				5,
				TimeUnit.MINUTES,
				new LinkedBlockingQueue<Runnable>());
		Collection<Future<?>> futures = new LinkedList<>();

		final String[] error = new String[1];
		for(final Appointment appointment : appointments)
			if((appointment.getStatus() == AppointmentStatus.LOCKED_FIT_DEFINITE) || (appointment.getStatus()
					== AppointmentStatus.LOCKED_FIT_POSSIBLE))
			{

				Runnable run = new Runnable()
				{
					@Override public void run()
					{
						FetchAppointmentDrivingAssignment fetchParticipations = new FetchAppointmentDrivingAssignment(userSettings
								.getRestUrl(), userSettings.getAuthToken(), appointment.getId());

						ActionResult<DrivingAssignment> result = fetchParticipations.execute();
						if(result.isSuccess())
							newDrivingAssigments.put(appointment.getId(), result.getValue());
						else
							error[0] = result.getShortErrorMessage();
					}
				};

				futures.add(threadPoolExecutor.submit(run));
			}

		waitForAllFutures(futures);

		if(error[0] != null)
			throw new UpdateException("Error fetching appointment participations", error[0]);
		else
			drivingAssignments = newDrivingAssigments;
	}


	// UPDATE UTIL
	private void waitForAllFutures(Iterable<Future<?>> futures)
	{
		for(Future<?> future : futures)
			try
			{
				future.get();
			}
			catch(InterruptedException ignored) {}
			catch(ExecutionException e)
			{
				e.printStackTrace();
			}
	}


	// UPDATE TASK
	public class UpdateDataTask extends AsyncTask<Void, Void, Void>
	{

		// TASK
		@Override protected Void doInBackground(Void... params)
		{
			try
			{
				updateCurrentUser();
				updateUsers();
				updateUserDrivenDistances();

				updateAppointments();
				updateParticipations();
				updateDrivingAssignments();
			}
			catch(UpdateException e)
			{
				System.out.println("update issue: "+e.getMessage());

				if(!isCancelled())
					new SimpleDialogue("Update issue: "+e.title, e.getMessage()).show();
			}

			return null;
		}

		@Override protected void onPostExecute(Void ignored)
		{
			for(Runnable runnable : runOnUpdateTasks)
				AndroidUtil.getForegroundActivity().runOnUiThread(runnable);

			sortByStartTime(false);
			updateDataTask = null;
		}

		@Override protected void onCancelled()
		{
			updateDataTask = null;
			clear(); // clear again to delete data loaded by this update
		}

	}


	// UPDATE EXCEPTION
	private static class UpdateException extends Exception
	{

		private final String title;


		// INIT
		public UpdateException(String title, String message)
		{
			super(message);

			this.title = title;
		}

	}

}
