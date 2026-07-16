from crewai import Task, Agent


def build_support_task(agent: Agent, question: str) -> Task:
    return Task(
        description=(
            f'Customer question: "{question}"\n\n'
            "First call the knowledge_base_search tool with this question "
            "(or a rephrased version of it) to retrieve relevant context. "
            "Answer using ONLY information the tool returns. If the tool "
            "returns nothing relevant, reply with exactly: "
            "'ESCALATE: ' followed by a one-sentence reason."
        ),
        expected_output="A direct answer to the customer, or a single ESCALATE line.",
        agent=agent,
    )


def build_content_task(agent: Agent, brief: dict) -> Task:
    return Task(
        description=(
            f"Write {brief['content_type']} content for platform "
            f"'{brief['platform']}'.\n"
            f"Topic: {brief['topic']}\n"
            f"Tone: {brief['tone']}\n"
            f"Target audience: {brief['audience']}\n"
            f"Max length: {brief.get('max_length', 280)} characters.\n\n"
            "If the topic needs current facts you don't already know, use "
            "the web_search tool first. Otherwise write directly."
        ),
        expected_output="The final copy only - no explanations, no preamble, no markdown fences.",
        agent=agent,
    )


def build_analysis_task(agent: Agent, file_path: str) -> Task:
    return Task(
        description=(
            f"Call the dataframe_summary tool with file_path='{file_path}' "
            "to load and summarize the dataset. Then identify the 3-5 most "
            "decision-relevant insights (trends, outliers, or risks). Cite "
            "specific numbers from the summary - never generic statements."
        ),
        expected_output="A short bulleted list of specific, numeric insights.",
        agent=agent,
    )
