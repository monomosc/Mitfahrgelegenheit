package mitfahgelegenheit.androidapp.gui;

import android.app.Activity;
import android.content.DialogInterface;
import android.content.DialogInterface.OnClickListener;
import android.content.DialogInterface.OnDismissListener;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AlertDialog.Builder;
import mitfahgelegenheit.androidapp.util.AndroidUtil;

public class SimpleDialogue
{

	private final String title;
	private final String message;

	private Runnable onClose = new Runnable()
	{
		@Override public void run()
		{

		}
	};


	// INIT
	public SimpleDialogue(String title, String message)
	{
		this.title = title;
		this.message = message;
	}

	public SimpleDialogue setOnClose(Runnable onClose)
	{
		this.onClose = onClose;
		return this;
	}


	// SHOW
	public void show()
	{
		final Activity foregroundActivity = AndroidUtil.getForegroundActivity();

		foregroundActivity.runOnUiThread(new Runnable()
		{
			@Override public void run()
			{
				Builder builder = new Builder(foregroundActivity);
				builder.setTitle(title).setPositiveButton("OK", new OnClickListener()
				{
					@Override public void onClick(DialogInterface dialog, int id)
					{
						onClose.run();
					}
				}).setMessage(message).setOnDismissListener(new OnDismissListener()
				{
					@Override public void onDismiss(DialogInterface dialogInterface)
					{
						onClose.run();
					}
				});

				AlertDialog alertDialog = builder.create();
				alertDialog.show();
			}
		});
	}

}
