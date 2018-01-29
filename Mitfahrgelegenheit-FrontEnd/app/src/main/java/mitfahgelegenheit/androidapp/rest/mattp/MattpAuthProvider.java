package mitfahgelegenheit.androidapp.rest.mattp;

import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import org.apache.http.impl.client.HttpClientBuilder;

public abstract class MattpAuthProvider
{

	protected abstract void provideAuthFor(HttpClientBuilder httpClientBuilder);

	protected abstract void provideAuthFor(MattpRequest request);

}
