package mitfahgelegenheit.androidapp.gui.activities;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.widget.TextView;
import mitfahgelegenheit.androidapp.R;
import mitfahgelegenheit.androidapp.model.user.User;

public class SingleUserViewActivity extends AppCompatActivity
{

	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_single_user_view);
		Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
		setSupportActionBar(toolbar);
		Intent intent = getIntent();
		int userId = intent.getExtras().getInt("userId");
		User user = AppointmentViewActivity.getDataContainer().findUserById(userId);

		TextView usernameView = findViewById(R.id.textUsernameV);
		usernameView.setText(user.getUsername());

		TextView emailView = findViewById(R.id.textEmailV);
		emailView.setText(user.getEmail());

		TextView phoneView = findViewById(R.id.textPhoneV);
		phoneView.setText(user.getPhoneNumber());

		TextView kmDrivenView = findViewById(R.id.textKmDrivenV);
		kmDrivenView.setText(""+AppointmentViewActivity.getDataContainer().getUserDistance(user.getId()));
	}

}
