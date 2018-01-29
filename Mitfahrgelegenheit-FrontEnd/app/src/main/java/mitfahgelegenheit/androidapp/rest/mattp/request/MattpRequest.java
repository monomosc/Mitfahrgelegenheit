package mitfahgelegenheit.androidapp.rest.mattp.request;

import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MattpRequest
{

	private final AbstractURL url;
	private final MattpMethod mattpMethod;

	private final List<MattpHeader> headers = new ArrayList<>();
	private MattpRequestBody body;

	public MattpRequest(AbstractURL url, MattpMethod mattpMethod)
	{
		this.url = url;
		this.mattpMethod = mattpMethod;
	}


	// INIT
	public static MattpRequest get(AbstractURL url)
	{
		return new MattpRequest(url, MattpMethod.GET);
	}

	public void addHeader(String key, String value)
	{
		addHeader(new MattpHeader(key, value));
	}

	public void addHeader(MattpHeader header)
	{
		headers.add(header);
	}


	// GETTERS
	public List<MattpHeader> getHeaders()
	{
		return Collections.unmodifiableList(headers);
	}

	public AbstractURL getUrl()
	{
		return url;
	}

	public MattpMethod getMattpMethod()
	{
		return mattpMethod;
	}

	public MattpRequestBody getBody()
	{
		return body;
	}

	public void setBody(MattpRequestBody body)
	{
		this.body = body;
	}

}
