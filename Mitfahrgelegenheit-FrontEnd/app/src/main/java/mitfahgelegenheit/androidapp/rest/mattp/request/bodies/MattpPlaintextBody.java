package mitfahgelegenheit.androidapp.rest.mattp.request.bodies;


import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequestBody;
import org.apache.commons.io.IOUtils;

import java.io.InputStream;
import java.nio.charset.Charset;


public class MattpPlaintextBody implements MattpRequestBody
{

	// CONSTANTS
	private static final Charset DEFAULT_CHARSET = Charset.forName("UTF-8");


	// ATTRIBUTES
	private final String text;
	private final Charset charset;


	// INIT
	public MattpPlaintextBody(String text)
	{
		this(text, DEFAULT_CHARSET);
	}

	public MattpPlaintextBody(String text, Charset charset)
	{
		this.text = text;
		this.charset = charset;
	}


	// BODY
	@Override public String getContentType()
	{
		return "text/plain";
	}

	@Override public InputStream getAsInputStream()
	{
		return IOUtils.toInputStream(text, charset);
	}

	@Override public long getStreamLength()
	{
		return text.getBytes(charset).length;
	}

}
