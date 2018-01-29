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
import mitfahgelegenheit.androidapp.model.user.User;
import mitfahgelegenheit.androidapp.rest.action.user.CreateUser;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.util.UserInputValidator;

public class RegisterActivity extends AppCompatActivity
{

	private EditText usernameET;
	private EditText emailET;
	private EditText passwordET;
	private EditText phoneET;

	// TASKS
	private UserRegisterTask registerTask = null;


	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_register);


		usernameET = findViewById(id.RegisterUsername);
		emailET = findViewById(id.RegisterEmail);
		passwordET = findViewById(id.RegisterPassword);
		phoneET = findViewById(id.RegisterPhone);
		usernameET = (EditText) findViewById(id.RegisterUsername);
		usernameET.setText(getIntent().getExtras().getString("username"));
		emailET = (EditText) findViewById(id.RegisterEmail);
		passwordET = (EditText) findViewById(id.RegisterPassword);
		passwordET.setText(getIntent().getExtras().getString("password"));
		phoneET = (EditText) findViewById(id.RegisterPhone);

		Button confirm = findViewById(id.RegisterUserData);
		confirm.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View v)
			{
				confirm();
			}
		});
	}

	private void confirm()
	{
		emailET.setError(null);
		passwordET.setError(null);
		phoneET.setError(null);
		usernameET.setError(null);

		View focusView = null;
		boolean cancel = false;

		String emailStr = emailET.getText().toString();
		String passwordStr = passwordET.getText().toString();
		String phoneNumberStr = phoneET.getText().toString();
		String usernameStr = usernameET.getText().toString();

		if(!UserInputValidator.isUserNameValid(usernameStr))
		{
			usernameET.setError(getString(string.error_invalid_username));
			focusView = usernameET;
			cancel = true;
		}
		if(!UserInputValidator.isPhoneValid(phoneNumberStr))
		{
			phoneET.setError(getString(string.error_invalid_phone_number));
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
			User user = new User(-1, 0, usernameStr, emailStr, phoneNumberStr);

			registerTask = new UserRegisterTask(user, passwordStr);
			registerTask.execute((Void) null);
		}

	}


	// TASK
	public class UserRegisterTask extends AsyncTask<Void, Void, Boolean>
	{

		private final User user;
		private final String password;


		public UserRegisterTask(User user, String password)
		{
			this.user = user;
			this.password = password;
		}


		// TASK
		@Override protected Boolean doInBackground(Void... params)
		{
			AbstractURL restUrl = UserSettings.load(RegisterActivity.this).getRestUrl();
			CreateUser createUser = new CreateUser(restUrl, user, password);
			ActionResult<Void> result = createUser.execute();

			Runnable onSuccessClose = new Runnable()
			{
				@Override public void run()
				{
					finish();
				}
			};

			if(result.isSuccess())
				new SimpleDialogue("Registration complete", "Registered with username '"+user.getUsername()+"'")
						.setOnClose(onSuccessClose)
						.show();
			else
				new SimpleDialogue("Registration error", result.getShortErrorMessage()).show();

			return result.isSuccess();
		}

		@Override protected void onPostExecute(Boolean success)
		{
			registerTask = null;

			if(success)
				UserSettings.load(RegisterActivity.this).setUsername(user.getUsername());
		}

		@Override protected void onCancelled()
		{
			registerTask = null;

		}

	}

}
