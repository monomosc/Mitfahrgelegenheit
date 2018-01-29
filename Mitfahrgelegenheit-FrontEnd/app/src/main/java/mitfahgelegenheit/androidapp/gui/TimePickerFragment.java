package mitfahgelegenheit.androidapp.gui;

import android.app.Dialog;
import android.app.DialogFragment;
import android.app.TimePickerDialog;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.widget.TimePicker;
import java.util.Calendar;
import java.util.Date;

import mitfahgelegenheit.androidapp.gui.activities.AddNewAppmntActivity;


public class TimePickerFragment extends DialogFragment
        implements TimePickerDialog.OnTimeSetListener {

    private Calendar c;

    @Override
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        // Use the current time as the default values for the picker
        final Date date = AddNewAppmntActivity.getDateContainer().getDate();
        c = Calendar.getInstance();
        c.setTime(date);
        int hour = c.get(Calendar.HOUR_OF_DAY);
        int minute = c.get(Calendar.MINUTE);

        // Create a new instance of TimePickerDialog and return it
        return new TimePickerDialog(getActivity(), this, hour, minute,
                DateFormat.is24HourFormat(getActivity()));
    }

    public void onTimeSet(TimePicker view, int hourOfDay, int minute) {
        // Do something with the time chosen by the user
        c.set(Calendar.HOUR_OF_DAY,hourOfDay);
        c.set(Calendar.MINUTE,minute);
        AddNewAppmntActivity.getDateContainer().changeDate(c.getTime());
    }
}
