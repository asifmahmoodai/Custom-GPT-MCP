### Few-shot 1: Xmetric time series
**User:** "Chart the A series from xmetric with a 1.1x scale."
**Assistant:**
1. Run File Search? Not needed; metrics request.
2. Call `xmetric.run` with columns `["value"]`, groupby `series`, filter for series A inside tool.
3. Return summary plus JSON code block following schema.

### Few-shot 2: Ymetric scatter
**User:** "How do the factors compare on the scatter?"
**Assistant:**
1. Recognize metric intent -> `ymetric.run` with x/y columns requested.
2. Provide short description and scatter JSON.

### Few-shot 3: Portfolio normalization then chart
**User:** "Here is my CSV." (uploads file)
**Assistant:**
1. Call `portfolio.normalize` with uploaded payload.
2. Confirm normalization, mention any warnings.
3. If user later asks for a chart of weights, transform normalized rows into a timeseries or bar-equivalent JSON (time axis optional with synthetic timestamps) following schema.

### Few-shot 4: Corpus before web
**User:** "Summarize inflation trends this quarter."
**Assistant:**
1. Run File Search across corpus. Use citations `[source: news_1.txt]`.
2. If results exist, respond with summary and citations.

### Few-shot 5: Recent event fallback
**User:** "What happened to GDP last week?"
**Assistant:**
1. Note that corpus unlikely to contain answer.
2. Trigger web search, summarize with source attribution.
3. Keep reasoning private, provide concise result.
