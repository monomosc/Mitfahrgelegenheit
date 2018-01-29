package mitfahgelegenheit.androidapp.rest.serialization.tostring;

public interface FromStringDeserializer<T>
{

	T deserialize(String objectString);

}
