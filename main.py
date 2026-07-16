import typer
import uvicorn
from fastapi import FastAPI
from api.router import router
from config.settings import settings
from database.task_history import task_history

app = FastAPI(title=settings.APP_NAME)
app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize database schema on startup."""
    await task_history.initialize_schema()

cli = typer.Typer(help="Omni-Agent SaaS control CLI")


@cli.command()
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    uvicorn.run("main:app", host=host, port=port, reload=reload)


@cli.command()
def ask(question: str):
    """Ask the support bot a question directly from the CLI - no server needed."""
    from crewai import Crew
    from core.agents import EnterpriseAgentPool
    from core.tasks import build_support_task

    pool = EnterpriseAgentPool()
    agent = pool.get_customer_support_agent()
    task = build_support_task(agent, question)
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    typer.echo(str(crew.kickoff()))


@cli.command()
def seed_kb():
    """Seed the knowledge base with sample FAQ data."""
    from scripts.seed_knowledge_base import main as seed_main
    seed_main()


if __name__ == "__main__":
    cli()
