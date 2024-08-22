SUMMARY_PROMPT = f"""
    Give me a summary of the medical report in laymen terms? Any person that does not have much understanding \
    about the medical term should be able to understand.
"""
REPORT_PROMPT = f"""
    Extract the parameter reading from the biomedical report. \
    Format your response as a list of JSON object with \
    "Parameter", "Result", "Biological Reference Range" and "Method" as the keys. \
    If the information isn't present, use "unknown" as the value.
    """