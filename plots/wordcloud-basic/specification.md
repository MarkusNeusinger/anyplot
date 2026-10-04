# wordcloud-basic: Basic Word Cloud

## Description

A word cloud displays text data where word size represents frequency or importance. Words are arranged to fill available space, creating a visual summary of text content that highlights prominent terms and patterns. This visualization is ideal for quickly identifying the most common themes or keywords in a body of text.

## Applications

- Analyzing survey responses to identify common themes and feedback patterns
- Visualizing social media content to understand trending topics and sentiment
- Creating document summaries to highlight key terms in reports or articles
- Exploring text corpora to understand term distribution across documents

## Data

- `word` (text) - Individual words or short phrases to display
- `frequency` (numeric) - Count or importance score determining word size
- Size: 20-200 words typical for readability
- Example: Term frequencies extracted from document analysis or survey responses

## Notes

- Words should be preprocessed (one form per term with case variants merged, stop words removed): common words in lowercase; acronyms and proper nouns keep their usual case
- Very long words may need truncation for proper display
- Color can be decorative or encode additional information like category
- Libraries may use different algorithms for word placement (spiral, rectangular, etc.)

## What a good version looks like

- A good version shows: word size growing with frequency or importance, so the most frequent words are plainly the largest and the size range runs down to small but still readable words.
- A good version shows: words placed by the layout algorithm, not by data, so no axes or grid, arranged to fill the cloud's area with no word covering or touching another and none cut off at the edge.
- A good version shows: preprocessed text, as the Notes ask: stop words absent, each term appearing once rather than in several spellings or capitalizations, common words in lowercase and acronyms and proper nouns in their usual case.
- A good version shows: color either decorative or encoding one more property such as category, as the Notes allow; when it encodes something a legend or key says what, and every word stays readable against the page in both themes.
- A good version shows: the basic variant's words only: no second cloud for comparison, reference lines, highlighted words set apart by boxes, outlines or underlines, or callouts.
- Expected, not a defect: words of very different size, rotated words, an irregular outline, small gaps the layout could not fill, a long word shortened to fit, and long words that look heavier than short ones of the same frequency.
