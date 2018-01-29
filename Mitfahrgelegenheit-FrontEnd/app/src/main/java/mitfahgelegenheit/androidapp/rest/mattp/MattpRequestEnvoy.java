package mitfahgelegenheit.androidapp.rest.mattp;

import android.support.annotation.NonNull;
import mitfahgelegenheit.androidapp.rest.mattp.authproviders.NoAuthProvider;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpHeader;
import mitfahgelegenheit.androidapp.rest.mattp.request.MattpRequest;
import mitfahgelegenheit.androidapp.rest.mattp.response.MattpResponseBodyReader;
import mitfahgelegenheit.androidapp.rest.mattp.response.RequestResponse;
import mitfahgelegenheit.androidapp.rest.mattp.response.readers.MattpStringReader;
import mitfahgelegenheit.androidapp.rest.mattp.response.responses.ConnectionError;
import mitfahgelegenheit.androidapp.rest.mattp.response.responses.RequestFailure;
import mitfahgelegenheit.androidapp.rest.mattp.response.responses.RequestSuccess;
import mitfahgelegenheit.androidapp.util.MyOptional;
import mitfahgelegenheit.androidapp.util.ReturnOrTimeout;
import mitfahgelegenheit.androidapp.util.MySupplier;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.apache.http.HttpEntityEnclosingRequest;
import org.apache.http.HttpMessage;
import org.apache.http.StatusLine;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpHead;
import org.apache.http.client.methods.HttpOptions;
import org.apache.http.client.methods.HttpPatch;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.methods.HttpTrace;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.entity.InputStreamEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.client.HttpClients;

import java.io.IOException;
import java.io.InputStream;

public class MattpRequestEnvoy<T>
{

	// CONSTANTS
	private static final int CONNECTION_TIMEOUT_MS = 5*1000;

	// REQUEST
	private final MattpRequest request;
	private MattpAuthProvider authProvider = new NoAuthProvider();

	// RESPONSE
	private final MattpResponseBodyReader<T> responseBodyReader;


	// INIT
	public MattpRequestEnvoy(MattpRequest request, MattpResponseBodyReader<T> responseBodyReader)
	{
		this.request = request;
		this.responseBodyReader = responseBodyReader;
	}


	// SEND
	public RequestResponse<T> send()
	{
		ReturnOrTimeout<RequestResponse<T>> returnOrTimeout = new ReturnOrTimeout<>(new MySupplier<RequestResponse<T>>()
		{
			@Override public RequestResponse<T> get()
			{
				return sendWithoutTimeout();
			}
		}, CONNECTION_TIMEOUT_MS);

		MyOptional<RequestResponse<T>> responseOptional = returnOrTimeout.run();
		if(responseOptional.isPresent())
			return responseOptional.get();

		return new ConnectionError<>("Failed to connect to server: connection timed out");
	}

	@NonNull private RequestResponse<T> sendWithoutTimeout()
	{
		CloseableHttpClient httpClient = buildHttpClient();
		HttpUriRequest apacheRequest = buildApacheRequest();

		CloseableHttpResponse response = null;
		try
		{
			response = httpClient.execute(apacheRequest);
			return processResponse(response);
		}
		catch(IOException e)
		{
			return new ConnectionError<>(ExceptionUtils.getStackTrace(e));
		}
		finally
		{
			try
			{
				if(response != null)
					response.close();
			}
			catch(IOException e)
			{
				return new ConnectionError<>(ExceptionUtils.getStackTrace(e));
			}
		}
	}


	// RESPONSE
	private RequestResponse<T> processResponse(org.apache.http.HttpResponse response) throws IOException
	{
		mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine statusLine = convertApacheToDomainStatusLine(response.getStatusLine());

		if(didRequestFail(response))
			return new RequestFailure<>(statusLine, readResponseBodyOnFailure(response));

		return new RequestSuccess<>(statusLine, readResponseBodyOnSuccess(response));
	}

	private T readResponseBodyOnSuccess(org.apache.http.HttpResponse response) throws IOException
	{
		return readResponseBody(response, responseBodyReader);
	}

	private String readResponseBodyOnFailure(org.apache.http.HttpResponse response) throws IOException
	{
		return readResponseBody(response, new MattpStringReader());
	}

	private <BodyT> BodyT readResponseBody(org.apache.http.HttpResponse response, MattpResponseBodyReader<BodyT> reader)
			throws IOException
	{
		InputStream responseBodyStream = null;
		try
		{
			responseBodyStream = response.getEntity().getContent();
			return reader.read(responseBodyStream);
		}
		finally
		{
			if(responseBodyStream != null)
				responseBodyStream.close();
		}
	}


	// BUILD CLIENT
	private CloseableHttpClient buildHttpClient()
	{
		HttpClientBuilder clientBuilder = HttpClients.custom().useSystemProperties();
		authProvider.provideAuthFor(clientBuilder);

		RequestConfig requestConfig = RequestConfig
				.custom()
				.setConnectionRequestTimeout(CONNECTION_TIMEOUT_MS)
				.setConnectTimeout(CONNECTION_TIMEOUT_MS)
				.setSocketTimeout(CONNECTION_TIMEOUT_MS)
				.build();
		clientBuilder.setDefaultRequestConfig(requestConfig);

		return clientBuilder.build();
	}


	// BUILD REQUEST
	private HttpUriRequest buildApacheRequest()
	{
		authProvider.provideAuthFor(request);
		HttpUriRequest apacheRequest = getRawMethodRequest();

		addHeadersToRequest(apacheRequest);
		if(request.getBody() != null)
			addBodyToRequest(apacheRequest);

		return apacheRequest;
	}

	private HttpUriRequest getRawMethodRequest()
	{
		AbstractURL url = request.getUrl();

		switch(request.getMattpMethod())
		{
			case GET:
				return new HttpGet(url.toString());
			case HEAD:
				return new HttpHead(url.toString());
			case POST:
				return new HttpPost(url.toString());
			case PUT:
				return new HttpPut(url.toString());
			case DELETE:
				return new HttpDelete(url.toString());
			case TRACE:
				return new HttpTrace(url.toString());
			case OPTIONS:
				return new HttpOptions(url.toString());
			case PATCH:
				return new HttpPatch(url.toString());
		}

		throw new RuntimeException("should never happen");
	}

	private void addHeadersToRequest(HttpMessage apacheRequest)
	{
		for(MattpHeader header : request.getHeaders())
			apacheRequest.addHeader(header.getKey(), header.getValue());
	}

	private void addBodyToRequest(HttpMessage apacheRequest)
	{
		apacheRequest.addHeader("Content-Type", request.getBody().getContentType());
		((HttpEntityEnclosingRequest) apacheRequest).setEntity(new InputStreamEntity(request.getBody().getAsInputStream(),
				request.getBody().getStreamLength()));
	}


	// UTIL
	private mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine convertApacheToDomainStatusLine(StatusLine apacheStatusLine)
	{
		return new mitfahgelegenheit.androidapp.rest.mattp.response.StatusLine(apacheStatusLine.getProtocolVersion().toString(),
				apacheStatusLine.getStatusCode(),
				apacheStatusLine.getReasonPhrase());
	}


	// CONDITION UTIL
	private boolean didRequestFail(org.apache.http.HttpResponse response)
	{
		int statusCode = response.getStatusLine().getStatusCode();
		int statusCodeFirstDigit = statusCode/100;
		return statusCodeFirstDigit != 2;
	}

	public void setAuthProvider(MattpAuthProvider authProvider)
	{
		this.authProvider = authProvider;
	}
}
