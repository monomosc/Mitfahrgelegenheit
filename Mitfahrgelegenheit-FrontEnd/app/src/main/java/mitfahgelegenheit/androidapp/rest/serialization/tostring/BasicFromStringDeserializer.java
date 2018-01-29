package mitfahgelegenheit.androidapp.rest.serialization.tostring;

import mitfahgelegenheit.androidapp.rest.serialization.GsonUtil;

public class BasicFromStringDeserializer<T> implements FromStringDeserializer<T>
{

	// ATTRIBUTES
	private final Class<T> classToSerialize;


	// INIT
	public BasicFromStringDeserializer(Class<T> classToSerialize)
	{
		this.classToSerialize = classToSerialize;
	}


	// SERIALIZE
	@Override public T deserialize(String projectString)
	{
		return GsonUtil.get().fromJson(projectString, classToSerialize);
	}

}
