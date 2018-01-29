package mitfahgelegenheit.androidapp.util;

import java.util.ArrayList;
import java.util.List;

public final class PHR
{

	// CONSTANTS
	private static final String PLACEHOLDER = "{}";


	// INIT
	private PHR()
	{
	}


	// REPLACE
	public static String r(String text, Object... values)
	{
		List<Integer> placeholderIndices = determinePlaceholderIndices(text);

		if(placeholderIndices.size() != values.length)
			throw new IllegalArgumentException("given values: "+values.length+", found placeholders: "+placeholderIndices.size());

		return replacePlaceholdersWithValues(text, placeholderIndices, values);
	}

	private static List<Integer> determinePlaceholderIndices(String text)
	{
		List<Integer> placeholderIndices = new ArrayList<>();
		int searchFrom = 0;
		while(true)
		{
			int index = text.indexOf(PLACEHOLDER, searchFrom);
			if(index == -1)
				break;

			placeholderIndices.add(index);
			searchFrom = index+1;
		}

		return placeholderIndices;
	}

	private static String replacePlaceholdersWithValues(String text, List<Integer> placeholderIndices, Object[] values)
	{
		String filledInString = text;

		// iterate from back so inserting string doesn't change the indices of the other placeholders
		for(int i = placeholderIndices.size()-1; i >= 0; i--)
		{
			int placeholderStartIndex = placeholderIndices.get(i);

			String beforePlaceholder = filledInString.substring(0, placeholderStartIndex);
			String valueForPlaceholder = (values[i] == null) ? "null" : values[i].toString();
			String afterPlaceholder = filledInString.substring(placeholderStartIndex+PLACEHOLDER.length());

			filledInString = beforePlaceholder+valueForPlaceholder+afterPlaceholder;
		}

		return filledInString;
	}

}
