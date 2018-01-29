package mitfahgelegenheit.androidapp.rest.mattp.request;

import java.io.InputStream;

public interface MattpRequestBody
{

	String getContentType();


	InputStream getAsInputStream();

	long getStreamLength();

}
