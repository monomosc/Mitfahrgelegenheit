package mitfahgelegenheit.androidapp.rest.mattp.request;

public enum MattpMethod
{

	GET(true),
	HEAD(true),
	OPTIONS(true),
	TRACE(true),

	POST(false),
	PUT(false),
	DELETE(false),
	PATCH(false);


	// ATTRIBUTES
	public final boolean safe;

	MattpMethod(boolean safe)
	{
		this.safe = safe;
	}
}
