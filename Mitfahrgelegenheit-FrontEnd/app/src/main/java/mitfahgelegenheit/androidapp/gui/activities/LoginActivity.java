package mitfahgelegenheit.androidapp.gui.activities;

import android.R.integer;
import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.annotation.TargetApi;
import android.content.Context;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Build.VERSION_CODES;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.KeyEvent;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.inputmethod.EditorInfo;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.TextView.OnEditorActionListener;
import mitfahgelegenheit.androidapp.R.id;
import mitfahgelegenheit.androidapp.R.layout;
import mitfahgelegenheit.androidapp.R.string;
import mitfahgelegenheit.androidapp.UserSettings;
import mitfahgelegenheit.androidapp.gui.SimpleDialogue;
import mitfahgelegenheit.androidapp.model.user.Credentials;
import mitfahgelegenheit.androidapp.rest.action.FetchAuthToken;
import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;
import mitfahgelegenheit.androidapp.util.MyOptional;
import mitfahgelegenheit.androidapp.util.UserInputValidator;

public class LoginActivity extends AppCompatActivity
{

	// UI
	private AutoCompleteTextView mUsernameView;
	private EditText mPasswordView;
	private EditText restUrlView;

	private View mProgressView;
	private View mLoginFormView;
	private Context context;

	// TASKS
	private UserLoginTask mAuthTask = null;


	@Override protected void onResume()
	{
		super.onResume();

		mPasswordView.setText("");
	}


	// INIT
	@Override protected void onCreate(Bundle savedInstanceState)
	{
		super.onCreate(savedInstanceState);
		setContentView(layout.activity_login);
		context = this;

		mUsernameView = findViewById(id.email);
		mPasswordView = findViewById(id.password);
		mPasswordView.setOnEditorActionListener(new OnEditorActionListener()
		{
			@Override public boolean onEditorAction(TextView textView, int id, KeyEvent keyEvent)
			{
				if((id == EditorInfo.IME_ACTION_DONE) || (id == EditorInfo.IME_NULL))
				{
					attemptLogin();
					return true;
				}

				return false;
			}
		});
		mUsernameView.setText(UserSettings.load(this).getUsername());


		Button mEmailSignInButton = findViewById(id.email_sign_in_button);
		mEmailSignInButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				attemptLogin();
			}
		});

		Button mEmailRegisterButton = findViewById(id.email_register_button);
		mEmailRegisterButton.setOnClickListener(new OnClickListener()
		{
			@Override public void onClick(View view)
			{
				attemptRegister();
			}
		});

		mLoginFormView = findViewById(id.login_form);
		mProgressView = findViewById(id.login_progress);


		restUrlView = findViewById(id.editRestUrl);
		restUrlView.setText(UserSettings.load(this).getRestUrl().toString());
		restUrlView.addTextChangedListener(new TextWatcher()
		{
			@Override public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {}

			@Override public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {}

			@Override public void afterTextChanged(Editable editable)
			{
				updateRestUrl();
			}
		});

		mUsernameView.requestFocus();
	}

	private void attemptRegister()
	{
		Intent intent = new Intent(context, RegisterActivity.class);
		intent.putExtra("username", mUsernameView.getText().toString());
		intent.putExtra("password", mPasswordView.getText().toString());
		startActivity(intent);
	}

	private void attemptLogin()
	{
		if(mAuthTask != null)
			return;

		MyOptional<Credentials> credentialsOptional = validateAndGetCredentials();
		if(!credentialsOptional.isPresent())
			return;

		showProgressSpinner();
		mAuthTask = new UserLoginTask(credentialsOptional.get());
		mAuthTask.execute((Void) null);
	}

	private MyOptional<Credentials> validateAndGetCredentials()
	{
		mUsernameView.setError(null);
		mPasswordView.setError(null);

		String username = mUsernameView.getText().toString();
		String password = mPasswordView.getText().toString();

		boolean cancel = false;
		View focusView = null;


		// validate password
		if(!TextUtils.isEmpty(password) && !(password.length() > 3))
		{
			mPasswordView.setError(getString(string.error_invalid_password));
			focusView = mPasswordView;
			cancel = true;
		}


		// validate username
		if(TextUtils.isEmpty(username))
		{
			mUsernameView.setError(getString(string.error_field_required));
			focusView = mUsernameView;
			cancel = true;
		}
		else if(!UserInputValidator.isUserNameValid(username))
		{
			mUsernameView.setError(getString(string.error_invalid_username));
			focusView = mUsernameView;
			cancel = true;
		}

		if(cancel)
		{
			focusView.requestFocus();
			return MyOptional.empty();
		}

		return MyOptional.of(new Credentials(username, password));
	}


	// REST URL
	private void updateRestUrl()
	{
		String restUrl = restUrlView.getText().toString();
		UserSettings.load(this).setRestUrl(restUrl);
	}


	// PROGRESS
	private void showProgressSpinner()
	{
		showProgress(true);
	}

	private void hideProgressSpinner()
	{
		showProgress(false);
	}

	@TargetApi(VERSION_CODES.HONEYCOMB_MR2) private void showProgress(final boolean show)
	{
		int shortAnimTime = getResources().getInteger(integer.config_shortAnimTime);

		mLoginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
		mLoginFormView.animate().setDuration(shortAnimTime).alpha(show ? 0 : 1).setListener(new AnimatorListenerAdapter()
		{
			@Override public void onAnimationEnd(Animator animation)
			{
				mLoginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
			}
		});

		mProgressView.setVisibility(show ? View.VISIBLE : View.GONE);
		mProgressView.animate().setDuration(shortAnimTime).alpha(show ? 1 : 0).setListener(new AnimatorListenerAdapter()
		{
			@Override public void onAnimationEnd(Animator animation)
			{
				mProgressView.setVisibility(show ? View.VISIBLE : View.GONE);
			}
		});
	}


	// LOGIN TASK
	public class UserLoginTask extends AsyncTask<Void, Void, Boolean>
	{

		private final Credentials credentials;


		// INIT
		public UserLoginTask(Credentials credentials)
		{
			this.credentials = credentials;
		}


		// TASK
		@Override protected Boolean doInBackground(Void... params)
		{
			UserSettings userSettings = UserSettings.load(LoginActivity.this);

			AbstractURL restUrl = userSettings.getRestUrl();
			FetchAuthToken fetchAuthToken = new FetchAuthToken(restUrl, credentials.getUsername(), credentials.getPassword());
			ActionResult<String> result = fetchAuthToken.execute();

			if(result.isSuccess())
			{
				userSettings.setAuthToken(result.getValue());
				userSettings.setUsername(credentials.getUsername());
			}
			else
				showLoginIssueDialogue(result.getShortErrorMessage());

			return result.isSuccess();
		}

		@Override protected void onPostExecute(Boolean success)
		{
			mAuthTask = null;
			hideProgressSpinner();

			if(success)
			{
				startAppointmentView();
				finish();
			}
			else
				mPasswordView.requestFocus();
		}

		@Override protected void onCancelled()
		{
			mAuthTask = null;
			hideProgressSpinner();
		}

	}


	// INVALID CREDENTIALS DIALOG
	private void showLoginIssueDialogue(String error)
	{
		new SimpleDialogue("Login issue", error).show();
	}


	// NAVIGATION
	private void startAppointmentView()
	{
		Intent intent = new Intent(context, AppointmentViewActivity.class);
		startActivity(intent);
	}

}

