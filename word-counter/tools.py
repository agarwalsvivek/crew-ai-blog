from crewai.tools import tool

@tool("Word Counter")
def count_words(text: str) -> str:
    """Count the number of words in a given text."""
    return f"The text has {len(text.split())} words."