package mitfahgelegenheit.androidapp.rest.mattp.response;

import java.io.IOException;
import java.io.InputStream;

public interface MattpResponseBodyReader<T>
{

	T read(InputStream inputStream) throws IOException;

}
