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
import mitfahgelegenheit.androidapp.gui.activities.SingleAppmntViewActivity;
import mitfahgelegenheit.androidapp.model.appointment.Appointment;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.appointment.Participation;
import mitfahgelegenheit.androidapp.model.appointment.Participation.ParticipationType;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class ParticipationListViewAdapter extends BaseAdapter
{

	private final Context context;
	private static LayoutInflater inflater = null;

	private final LocalDataContainer data = AppointmentViewActivity.getDataContainer();
	private final List<Participation> participations = new ArrayList<>();


	// INIT
	public ParticipationListViewAdapter(@NonNull Context context)
	{
		this.context = context;
		inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);

		updateParticipations();
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
			ViewHolder vh;
			View view = convertView;

			if(convertView == null)
			{
				view = inflater.inflate(layout.participation_list_item, null);
				vh = new ViewHolder();
				vh.tv1 = view.findViewById(id.textPfrom);
				vh.tv2 = view.findViewById(id.textPto);
				vh.tv3 = view.findViewById(id.textPtime);
				vh.tv4 = view.findViewById(id.textPstatus);
				vh.tv5 = view.findViewById(id.textPcarLvl);
				vh.tv6 = view.findViewById(id.textPfreeSeats);
				view.setTag(vh);
			}
			else
				vh = (ViewHolder) view.getTag();

			if(participations.isEmpty())
				vh.tv3.setText("No Data");
			else
			{
				Participation participation = participations.get(position);
				Appointment appointment = data.getAppointmentById(participation.getAppointmentId());

				vh.tv1.setText("From: "+appointment.getStartLocation());
				vh.tv2.setText("To: "+appointment.getTargetLocation());
				vh.tv3.setText(""+appointment.timeToString());
				vh.tv4.setText(""+appointment.getStatus());
				vh.tv5.setText(""+participation.getParticipationType().displayName);
				if(participation.getParticipationType() == ParticipationType.NO_CAR)
					vh.tv6.setText("");
				else
					vh.tv6.setText(""+participation.getMaximumPassengers()+" seats (incl. driver)");

				view.setOnClickListener(new OnItemClickListener(position));
			}
			view.setOnClickListener(new OnItemClickListener(position));
			return view;

		}
		catch(RuntimeException e)
		{
			e.printStackTrace();
		}

		return convertView;
	}


	static class ViewHolder
	{
		TextView tv1, tv2, tv3, tv4, tv5, tv6;
	}


	private class OnItemClickListener implements OnClickListener
	{
		private final int mPosition;

		OnItemClickListener(int position)
		{
			mPosition = position;
		}

		@Override public void onClick(View arg0)
		{
			Intent intent = new Intent(context, SingleAppmntViewActivity.class);
			intent.putExtra("appointmentId", participations.get(mPosition).getAppointmentId());
			context.startActivity(intent);
		}
	}

	public void sortByTime(boolean desc)
	{
		Collections.sort(participations, new Comparator<Participation>()
		{
			@Override public int compare(Participation o1, Participation o2)
			{
				return timeOrder(o1, o2);
			}
		});
		updateAndReverse(desc);
	}

	public void sortByStatus(boolean desc)
	{
		final boolean descFinal = desc;
		Collections.sort(participations, new Comparator<Participation>()
		{
			@Override public int compare(Participation o1, Participation o2)
			{
				int o1Int = data.lifecycleToInt(data.getAppointmentById(o1.getAppointmentId()).getStatus(), descFinal);
				int o2Int = data.lifecycleToInt(data.getAppointmentById(o2.getAppointmentId()).getStatus(), descFinal);

				int compareInt = o1Int-o2Int;
				return (compareInt == 0) ? timeOrder(o1, o2) : compareInt;
			}
		});
		updateAndReverse(desc);
	}

	public void sortByDrivingLevel(boolean desc)
	{
		Collections.sort(participations, new Comparator<Participation>()
		{
			@Override public int compare(Participation o1, Participation o2)
			{
				if(o1.getParticipationType() == o2.getParticipationType())
					return timeOrder(o1, o2);

				return o1.getParticipationType().compareTo(o2.getParticipationType());
			}
		});
		updateAndReverse(desc);
	}

	private int timeOrder(Participation o1, Participation o2)
	{
		return data
				.getAppointmentById(o1.getAppointmentId())
				.getStartTimeAsDate()
				.compareTo(data.getAppointmentById(o2.getAppointmentId()).getStartTimeAsDate());
	}

	private void updateAndReverse(boolean desc)
	{
		if(desc)
			Collections.reverse(participations);

		notifyDataSetChanged();
	}


	public final void updateParticipations()
	{
		participations.clear();
		participations.addAll(data.getParticipationsOfCurrentUser());

		notifyDataSetChanged();
	}

}
