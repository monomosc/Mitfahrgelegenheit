package mitfahgelegenheit.androidapp.util;

import java.util.NoSuchElementException;

public final class MyOptional<T>
{

	private final T value;


	// INIT
	public static <T> MyOptional<T> empty()
	{
		return new MyOptional<>(null);
	}

	public static <T> MyOptional<T> of(T value)
	{
		if(value == null)
			throw new IllegalArgumentException("value can't be null");

		return ofNullable(value);
	}

	public static <T> MyOptional<T> ofNullable(T value)
	{
		return new MyOptional<>(value);
	}

	private MyOptional(T value)
	{
		this.value = value;
	}


	// OBJECT
	@Override public String toString()
	{
		return "MyOptional{"+"value="+value+'}';
	}


	// GETTERS
	public boolean isPresent()
	{
		return value != null;
	}

	public T get()
	{
		if(value == null)
			throw new NoSuchElementException("optional is empty");

		return value;
	}

}
