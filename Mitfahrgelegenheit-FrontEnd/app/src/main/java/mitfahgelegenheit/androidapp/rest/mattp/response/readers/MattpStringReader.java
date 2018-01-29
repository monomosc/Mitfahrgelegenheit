package mitfahgelegenheit.androidapp.rest.mattp.response.readers;


import mitfahgelegenheit.androidapp.rest.mattp.response.MattpResponseBodyReader;
import org.apache.commons.io.IOUtils;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.Charset;


public class MattpStringReader implements MattpResponseBodyReader<String>
{

	// CONSTANTS
	public static final Charset DEFAULT_CHARSET = Charset.forName("UTF-8");

	// SETTINGS
	private final Charset charset;


	// INIT
	public MattpStringReader()
	{
		charset = DEFAULT_CHARSET;
	}

	public MattpStringReader(Charset charset)
	{
		this.charset = charset;
	}


	// READ
	@Override public String read(InputStream inputStream) throws IOException
	{
		return IOUtils.toString(inputStream, charset);
	}

}
