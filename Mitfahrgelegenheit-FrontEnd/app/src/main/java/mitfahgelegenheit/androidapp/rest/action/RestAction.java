package mitfahgelegenheit.androidapp.rest.action;

import mitfahgelegenheit.androidapp.rest.mattp.AbstractURL;
import mitfahgelegenheit.androidapp.rest.mattp.MattpAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.authproviders.NoAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.authproviders.TokenAuthProvider;
import mitfahgelegenheit.androidapp.rest.result.ActionResult;

public abstract class RestAction<T>
{

	protected final AbstractURL restUrl;
	protected final String authToken;


	// INIT
	protected RestAction(AbstractURL restUrl, String authToken)
	{
		this.restUrl = restUrl;
		this.authToken = authToken;
	}


	protected MattpAuthProvider getAuthProvider()
	{
		if(authToken == null)
			return new NoAuthProvider();

		return new TokenAuthProvider(authToken);
	}

	public abstract ActionResult<T> execute();

}
