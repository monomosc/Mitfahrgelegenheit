package mitfahgelegenheit.androidapp.rest.serialization.tostring;

import com.google.gson.reflect.TypeToken;
import mitfahgelegenheit.androidapp.rest.serialization.GsonUtil;

public class TypeFromStringDeserializer<T> implements FromStringDeserializer<T>
{

	// ATTRIBUTES
	private final TypeToken<T> typeToken;


	// INIT
	public TypeFromStringDeserializer(TypeToken<T> typeToken)
	{
		this.typeToken = typeToken;
	}


	// DESERIALIZE
	@Override public T deserialize(String projectString)
	{
		return GsonUtil.get().fromJson(projectString, typeToken.getType());
	}

}
