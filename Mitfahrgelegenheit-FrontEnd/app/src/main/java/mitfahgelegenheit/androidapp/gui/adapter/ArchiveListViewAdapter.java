package mitfahgelegenheit.androidapp.gui.adapter;

import android.content.Context;
import android.support.annotation.NonNull;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.CheckBox;

import mitfahgelegenheit.androidapp.gui.activities.AppointmentViewActivity;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
import mitfahgelegenheit.androidapp.model.user.User;

import java.util.ArrayList;

public class ArchiveListViewAdapter extends BaseAdapter
{

	private final Context context;
	private static LayoutInflater inflater = null;
	private final LocalDataContainer data = AppointmentViewActivity.getDataContainer();
	private final ArrayList<Participation> participations;
	private final int appointmentId;
	private ArrayList<CheckBox> boxes = new ArrayList<>();

	public ArchiveListViewAdapter(@NonNull Context context, int appointmentId)
	{
		this.context = context;
		this.appointmentId = appointmentId;
		inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
		participations = new ArrayList<>(data.getParticipationsForAppointment(appointmentId));
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

	@Override public View getView(int position, View convertView, ViewGroup parent)
	{
		try
		{
			View view = convertView;
			CheckBox checkBox = new android.widget.CheckBox(context);
			User user = data.findUserById(participations.get(position).getUserId());
			checkBox.setText(user.getUsername());
			checkBox.setTextSize(24);
			boxes.add(checkBox);
			view = checkBox;
			return view;

		}
		catch(RuntimeException e)
		{
			e.printStackTrace();
		}

		return convertView;
	}

	public ArrayList<CheckBox> getBoxes()
	{
		return boxes;
	}

	public ArrayList<Participation> getParticipations()
	{
		return participations;
	}

}
