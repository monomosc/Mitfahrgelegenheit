package mitfahgelegenheit.androidapp.rest.mattp.authproviders;

import mitfahgelegenheit.androidapp.rest.mattp.MattpAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import org.apache.http.impl.client.HttpClientBuilder;

public class NoAuthProvider extends MattpAuthProvider
{

	@Override protected void provideAuthFor(HttpClientBuilder httpClientBuilder)
	{
		// do nothing
	}

	@Override protected void provideAuthFor(MattpRequest request)
	{
		// nothing
	}

}
