package mitfahgelegenheit.androidapp.rest.mattp.response.readers;

import mitfahgelegenheit.androidapp.rest.mattp.response.MattpResponseBodyReader;

import java.io.InputStream;

public class MattpVoidReader implements MattpResponseBodyReader<Void>
{

	// READ
	@Override public Void read(InputStream inputStream)
	{
		return null;
	}

}
