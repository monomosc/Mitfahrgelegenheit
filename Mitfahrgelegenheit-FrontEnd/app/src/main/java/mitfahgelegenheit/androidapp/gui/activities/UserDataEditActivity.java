package mitfahgelegenheit.androidapp.gui.activities;

import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.EditText;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.R.string;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.model.LocalDataContainer;
import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.model.user.UserWithPassword;
import mitfahgelegenheit.androidapp.rest.action.user.EditUser;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.util.UserInputValidator;

public class UserDataEditActivity extends AppCompatActivity
{

	// DATA
	private final LocalDataContainer data = AppointmentViewActivity.getDataContainer();

	// UI
	private EditText usernameET, emailET, passwordET, phoneET;
	private User currentUser;
	private Button confirm;

	// UPDATE
	private UpdateUserDataTask updateUserDataTask;

	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_user_data_edit);
		currentUser = data.getCurrentUser();

		usernameET = findViewById(id.editUsername);
		usernameET.setText(currentUser.getUsername());

		emailET = findViewById(id.editEmail);
		emailET.setText(currentUser.getEmail());

		passwordET = findViewById(id.editPassword);

		phoneET = findViewById(id.editPhone);
		phoneET.setText(currentUser.getPhoneNumber());

		confirm = findViewById(id.changeUserData);
		confirm.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				confirm();
			}
		});
	}


	// UPDATE
	private void confirm()
	{
		//reset errors
		emailET.setError(null);
		passwordET.setError(null);
		phoneET.setError(null);
		usernameET.setError(null);
		View focusView = null;

		boolean cancel = false;
		String emailStr, passwordStr, phoneNumberStr, usernameStr;
		emailStr = emailET.getText().toString();
		passwordStr = passwordET.getText().toString();
		phoneNumberStr = phoneET.getText().toString();
		usernameStr = usernameET.getText().toString();

		if(!UserInputValidator.isUserNameValid(usernameStr))
		{
			usernameET.setError("this username is too short");
			focusView = usernameET;
			cancel = true;
		}
		if(!UserInputValidator.isPhoneValid(phoneNumberStr))
		{
			phoneET.setError("this phoneET number is invalid");
			focusView = phoneET;
			cancel = true;
		}
		if(!UserInputValidator.isPasswordValid(passwordStr))
		{
			passwordET.setError(getString(string.error_invalid_password));
			focusView = passwordET;
			cancel = true;
		}
		if(!UserInputValidator.isEmailValid(emailStr))
		{
			emailET.setError(getString(string.error_invalid_email));
			focusView = emailET;
			cancel = true;
		}

		if(cancel)
			focusView.requestFocus();
		else
		{
			if(updateUserDataTask != null)
				return;


			User currentUser = data.getCurrentUser();
			UserWithPassword userWithPassword = new UserWithPassword(currentUser.getId(),
					currentUser.getGlobalAdminStatus(),
					usernameStr,
					emailStr,
					phoneNumberStr,
					passwordStr);

			updateUserDataTask = new UpdateUserDataTask(userWithPassword);
			updateUserDataTask.execute((Void) null);
		}
	}

	public class UpdateUserDataTask extends AsyncTask<Void, Void, Boolean>
	{

		private final UserWithPassword newUser;


		// INIT
		public UpdateUserDataTask(UserWithPassword newUser)
		{
			this.newUser = newUser;
		}


		// TASK
		@Override protected Boolean doInBackground(Void... params)
		{
			UserSettings userSettings = UserSettings.load(UserDataEditActivity.this);
			EditUser editUser = new EditUser(userSettings.getRestUrl(), userSettings.getAuthToken(), newUser);

			Runnable onSuccessClose = new Runnable()
			{
				@Override public void run()
				{
					finish();
				}
			};

			ActionResult<Void> result = editUser.execute();
			if(result.isSuccess())
			{
				userSettings.setUsername(newUser.getUsername());
				new SimpleDialogue("User data update", "Update successful!")
						.setOnClose(onSuccessClose)
						.show();
			}
			else
				new SimpleDialogue("Error on user data update", result.getShortErrorMessage()).show();

			return false;
		}

		@Override protected void onPostExecute(Boolean success)
		{
			data.updateAsync();
			updateUserDataTask = null;
		}

		@Override protected void onCancelled()
		{
			updateUserDataTask = null;
		}

	}

}
