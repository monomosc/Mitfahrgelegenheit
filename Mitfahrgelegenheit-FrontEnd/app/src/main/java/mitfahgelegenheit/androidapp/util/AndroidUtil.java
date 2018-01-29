package mitfahgelegenheit.androidapp.util;

import android.app.Activity;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.util.Map;

public final class AndroidUtil
{

	public static Activity getForegroundActivity()
	{
		tryBlock:
		try
		{
			Class<?> activityThreadClass = Class.forName("android.app.ActivityThread");
			Object activityThread = activityThreadClass.getMethod("currentActivityThread").invoke(null);
			Field activitiesField = activityThreadClass.getDeclaredField("mActivities");
			activitiesField.setAccessible(true);

			Map<Object, Object> activities = (Map<Object, Object>) activitiesField.get(activityThread);
			if(activities == null)
				break tryBlock;

			for(Object activityRecord : activities.values())
			{
				Class<? extends Object> activityRecordClass = activityRecord.getClass();
				Field pausedField = activityRecordClass.getDeclaredField("paused");
				pausedField.setAccessible(true);
				if(!pausedField.getBoolean(activityRecord))
				{
					Field activityField = activityRecordClass.getDeclaredField("activity");
					activityField.setAccessible(true);
					Activity activity = (Activity) activityField.get(activityRecord);
					return activity;
				}
			}
		}
		catch(ClassNotFoundException e)
		{
			e.printStackTrace();
		}
		catch(IllegalAccessException e)
		{
			e.printStackTrace();
		}
		catch(InvocationTargetException e)
		{
			e.printStackTrace();
		}
		catch(NoSuchMethodException e)
		{
			e.printStackTrace();
		}
		catch(NoSuchFieldException e)
		{
			e.printStackTrace();
		}

		throw new IllegalStateException("can't access foreground activity");
	}

}
