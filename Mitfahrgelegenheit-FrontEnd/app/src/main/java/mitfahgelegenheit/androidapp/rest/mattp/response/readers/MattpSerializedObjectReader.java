package mitfahgelegenheit.androidapp.rest.mattp.response.readers;


import mitfahgelegenheit.androidapp.rest.mattp.response.MattpResponseBodyReader;
import mitfahgelegenheit.androidapp.rest.serialization.tostring.FromStringDeserializer;

import java.io.IOException;
import java.io.InputStream;


public class MattpSerializedObjectReader<T> implements MattpResponseBodyReader<T>
{

	private final MattpResponseBodyReader<String> stringReader;
	private final FromStringDeserializer<T> fromStringDeserializer;


	// INIT
	public MattpSerializedObjectReader(FromStringDeserializer<T> fromStringDeserializer)
	{
		stringReader = new MattpStringReader();
		this.fromStringDeserializer = fromStringDeserializer;
	}

	public MattpSerializedObjectReader(MattpResponseBodyReader<String> stringReader, FromStringDeserializer<T> fromStringDeserializer)
	{
		this.stringReader = stringReader;
		this.fromStringDeserializer = fromStringDeserializer;
	}


	// READ
	@Override public T read(InputStream inputStream) throws IOException
	{
		String json = stringReader.read(inputStream);

		// TODO don't do io exception throwing when json invalid, find other way

		T object;
		try
		{
			object = fromStringDeserializer.deserialize(json);
		}
		catch(RuntimeException e)
		{
			throw new IOException("Failed to deserialize object", e);
		}

		if(object == null)
			throw new IOException("deserialized object was null (json input: "+json+")");

		return object;
	}

}
