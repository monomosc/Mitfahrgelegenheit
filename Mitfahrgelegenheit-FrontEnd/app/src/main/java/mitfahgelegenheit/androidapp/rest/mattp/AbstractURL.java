package mitfahgelegenheit.androidapp.rest.mattp;

public class AbstractURL
{

	private final String url;


	// INIT
	public AbstractURL(String url)
	{
		String cleanedUrl = url;
		while(cleanedUrl.endsWith("/"))
			cleanedUrl = cleanedUrl.substring(0, cleanedUrl.length()-1);

		this.url = cleanedUrl;
	}

	public AbstractURL(AbstractURL base, String extension)
	{
		this(base.combineWith(extension));
	}

	private String combineWith(String extension)
	{
		String processedExtension = extension;
		if(!processedExtension.startsWith("/"))
			processedExtension = "/"+processedExtension;

		return url+processedExtension;
	}


	// OBJECT
	@Override public String toString()
	{
		return url;
	}

}

