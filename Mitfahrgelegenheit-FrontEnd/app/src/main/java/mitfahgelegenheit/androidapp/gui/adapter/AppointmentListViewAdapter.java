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
import mitfahgelegenheit.androidapp.model.LocalDataContainer;

import java.util.List;

/**
 * Created by Dark Meta on 13.01.2018.
 * Helps with creation of Appointment View fragments in listView
 */

public class AppointmentListViewAdapter extends BaseAdapter
{

	private final Context context;
	private static LayoutInflater inflater = null;
	private final LocalDataContainer data = AppointmentViewActivity.getDataContainer();

	public AppointmentListViewAdapter(@NonNull Context context)
	{
		this.context = context;
		inflater = (LayoutInflater) context.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
	}


	@Override public int getCount()
	{
		return data.getAppointments().size();
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
		TextView tv1, tv2, tv3, tv4, tv5;
	}

	@Override public View getView(int position, View convertView, ViewGroup parent)
	{
		try
		{
			ViewHolder vh;
			View view = convertView;

			if(convertView == null)
			{
				view = inflater.inflate(layout.appmnt_list_item, null);
				vh = new ViewHolder();
				vh.tv1 = view.findViewById(id.textFROM);
				vh.tv2 = view.findViewById(id.textTO);
				vh.tv3 = view.findViewById(id.textTIME);
				vh.tv4 = view.findViewById(id.textREPEAT);
				vh.tv5 = view.findViewById(id.textCYCLE);
				view.setTag(vh);
			}
			else
				vh = (ViewHolder) view.getTag();

			if(data.getAppointments().isEmpty())
				vh.tv3.setText("No Data");
			else
			{
				List<String> strings = data.getAppointmentsToString().get(position);
				int appointmentId = Integer.parseInt(strings.get(5));

				vh.tv1.setText(strings.get(0));
				vh.tv2.setText(strings.get(1));
				vh.tv3.setText(strings.get(2));
				vh.tv4.setText(strings.get(3));
				vh.tv5.setText(strings.get(4));
				view.setOnClickListener(new OnItemClickListener(appointmentId));
			}

			return view;

		}
		catch(RuntimeException e)
		{
			e.printStackTrace();
		}

		return convertView;
	}

	private class OnItemClickListener implements OnClickListener
	{

		private final int appointmentId;


		// INIT
		public OnItemClickListener(int appointmentId)
		{
			this.appointmentId = appointmentId;
		}


		@Override public void onClick(View arg0)
		{
			viewSingleAppointment(appointmentId);
		}

	}

	private void viewSingleAppointment(int appointmentId)
	{
		Intent intent = new Intent(context, SingleAppmntViewActivity.class);
		intent.putExtra("appointmentId", appointmentId);

		context.startActivity(intent);
	}

}
