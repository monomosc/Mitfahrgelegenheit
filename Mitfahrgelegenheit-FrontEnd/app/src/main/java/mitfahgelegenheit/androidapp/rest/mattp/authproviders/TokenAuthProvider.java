package mitfahgelegenheit.androidapp.rest.mattp.authproviders;


import mitfahgelegenheit.androidapp.rest.mattp.MattpAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import org.apache.http.impl.client.HttpClientBuilder;

public class TokenAuthProvider extends MattpAuthProvider
{

	private final String authToken;


	// INIT
	public TokenAuthProvider(String authToken)
	{
		this.authToken = authToken;
	}


	@Override protected void provideAuthFor(HttpClientBuilder httpClientBuilder)
	{
		// nothing
	}

	@Override protected void provideAuthFor(MattpRequest request)
	{
		request.addHeader("Authorization", "Bearer "+authToken);
	}

}
