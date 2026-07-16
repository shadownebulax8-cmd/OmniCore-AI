from crewai import Agent
from core.llm_providers import get_llm_string
from core.tools import knowledge_base_search_tool, dataframe_summary_tool, web_search_tool


class EnterpriseAgentPool:
    """
    Factory for the three production agents. Instantiate fresh per-request
    (it's cheap - the LLM string is just a config lookup) rather than
    holding it as a module-level singleton, so a .env change is picked up
    without restarting workers mid-flight.
    """

    def __init__(self):
        self.llm = get_llm_string()

    def get_customer_support_agent(self) -> Agent:
        return Agent(
            role="Enterprise Support Specialist",
            goal=(
                "Answer customer questions accurately using only what the "
                "knowledge_base_search tool returns. Never invent an answer "
                "that isn't backed by retrieved context."
            ),
            backstory=(
                "You are a senior support engineer who has read the entire "
                "product knowledge base. You are precise, empathetic, and "
                "honest when you don't know something."
            ),
            tools=[knowledge_base_search_tool],
            verbose=True,
            memory=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def get_content_generation_agent(self) -> Agent:
        return Agent(
            role="Strategic Brand Copywriter",
            goal=(
                "Write high-conversion marketing copy that matches the "
                "requested platform, tone, audience, and length exactly."
            ),
            backstory=(
                "An expert marketing strategist who adapts voice per brief, "
                "researches current facts when needed, and never pads copy "
                "with generic filler."
            ),
            tools=[web_search_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def get_data_automation_agent(self) -> Agent:
        return Agent(
            role="Senior Systems Automation Analyst",
            goal=(
                "Turn raw spreadsheet data into concrete, numeric, "
                "decision-ready insights - never vague generalities."
            ),
            backstory=(
                "A data-engineering agent trained to spot trends, outliers, "
                "and risks in operational datasets."
            ),
            tools=[dataframe_summary_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
