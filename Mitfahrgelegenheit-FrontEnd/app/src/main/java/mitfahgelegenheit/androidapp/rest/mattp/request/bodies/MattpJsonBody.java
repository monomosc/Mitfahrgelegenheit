package mitfahgelegenheit.androidapp.rest.mattp.request.bodies;

import java.nio.charset.Charset;


public class MattpJsonBody extends MattpPlaintextBody
{

	// INIT
	 public MattpJsonBody(String text, Charset charset)
	{
		super(text, charset);
	}

	 public MattpJsonBody(String text)
	{
		super(text);
	}


	// BODY
	@Override public String getContentType()
	{
		return "application/json";
	}

}
