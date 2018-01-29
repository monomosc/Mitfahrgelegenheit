package mitfahgelegenheit.androidapp.util;

public class ReturnOrTimeout<T>
{

	// DEPENDENCIES
	private final MySupplier<T> toReturn;

	// SETTINGS
	private final long timeoutMs;


	// INIT
	public ReturnOrTimeout(MySupplier<T> toReturn, long timeoutMs)
	{
		this.toReturn = toReturn;
		this.timeoutMs = timeoutMs;
	}


	// RUN
	public MyOptional<T> run()
	{
		RunnableWithReturn run = new RunnableWithReturn();

		long startInstantMs = System.currentTimeMillis();
		Thread runThread = createAndStartThread(run, Thread.currentThread().getName()+"-TO");

		while(runThread.isAlive())
		{
			long timePassedMs = System.currentTimeMillis()-startInstantMs;

			if(timePassedMs > timeoutMs)
			{
				runThread.interrupt();
				return MyOptional.empty();
			}

			sleep(1);
		}

		return MyOptional.of(run.value);
	}


	// HELPER CLASSES
	private class RunnableWithReturn implements Runnable
	{

		private volatile T value;


		@Override public void run()
		{
			value = toReturn.get();
		}

	}


	// THREAD
	private static boolean sleep(long ms)
	{
		try
		{
			Thread.sleep(ms);
			return true;
		}
		catch(InterruptedException ignored)
		{
			Thread.currentThread().interrupt();
			return false;
		}
	}


	private static Thread createAndStartThread(Runnable runnable, String threadName)
	{
		Thread thread = new Thread(runnable);
		thread.setName(threadName);

		thread.start();
		return thread;
	}

}
