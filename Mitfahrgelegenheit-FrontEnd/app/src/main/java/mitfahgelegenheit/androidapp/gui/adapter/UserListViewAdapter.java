package mitfahgelegenheit.androidapp.gui.adapter;

import android.content.Context;
import android.content.Intent;
import android.support.annotation.NonNull;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.gui.activities.AppointmentViewActivity;
import mitfahgelegenheit.androidapp.gui.activities.SingleUserViewActivity;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.appointment.DrivingAssignment;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
import mitfahgelegenheit.androidapp.model.appointment.Participation.ParticipationType;
import mitfahgelegenheit.androidapp.model.user.User;

import java.util.ArrayList;
import java.util.List;

public class UserListViewAdapter extends BaseAdapter
{

	private final Context context;
	private static LayoutInflater inflater = null;
	private final LocalDataContainer data = AppointmentViewActivity.getDataContainer();
	private final int appointmentId;
	private List<Participation> participations;


	// INIT
	public UserListViewAdapter(@NonNull Context context, int appointmentId)
	{
		this.context = context;
		this.appointmentId = appointmentId;
		inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
		update();
	}

	public final void update()
	{
		participations = new ArrayList<>(data.getParticipationsForAppointment(appointmentId));
		notifyDataSetChanged();
	}


	@Override public int getCount()
	{
		return participations.size();
	}

	@Override public Object getItem(int position)
	{
		return position;
	}

	@Override public long getItemId(int position)
	{
		return position;
	}

	class ViewHolder
	{
		TextView tv1, tv2;
	}

	@Override public View getView(int position, View convertView, ViewGroup parent)
	{
		try
		{
			ViewHolder vh;
			View view = convertView;

			if(convertView == null)
			{
				view = inflater.inflate(layout.participating_user_list_item, null);
				vh = new ViewHolder();
				vh.tv1 = view.findViewById(id.partUserName);
				vh.tv2 = view.findViewById(id.partUSerDriver);
				view.setTag(vh);
			}
			else
				vh = (ViewHolder) view.getTag();

			Participation participation = participations.get(position);

			User user = data.findUserById(participation.getUserId());
			vh.tv1.setText("  "+user.getUsername());

			String participationText = "";
			DrivingAssignment assignment = data.getDrivingAssignment(appointmentId);

			if(assignment == null)
			{
				participationText = participation.getParticipationType().displayName;
				if(participation.getParticipationType() != ParticipationType.NO_CAR)
					participationText += " ("+participation.getMaximumPassengers()+" seats)";
			}
			else
			{
				User driver = data.findUserById(assignment.getDriverUserIdOf(user.getId()));

				if(user.getId() == driver.getId())
					participationText = "drives "+assignment.getNumberOfParticipantsOfDriver(driver.getId())+" (max: "
							+participation.getMaximumPassengers()+")";
				else
					participationText = "Driver: "+driver.getUsername();
			}
			vh.tv2.setText(participationText+"  ");

			view.setOnClickListener(new OnItemClickListener(user.getId()));
			return view;
		}
		catch(RuntimeException e)
		{
			throw new RuntimeException(e);
		}
	}

	private class OnItemClickListener implements OnClickListener
	{

		private final int userId;


		// INIT
		public OnItemClickListener(int userId)
		{
			this.userId = userId;
		}


		@Override public void onClick(View arg0)
		{
			showUserInformation(userId);
		}

	}

	private void showUserInformation(int userId)
	{
		Intent intent = new Intent(context, SingleUserViewActivity.class);
		intent.putExtra("userId", userId);
		context.startActivity(intent);
	}

}

