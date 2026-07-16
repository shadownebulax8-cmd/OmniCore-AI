import openpyxl
import pandas as pd
from crewai import Crew
from workers.celery_app import celery_app
from workers.email_worker import send_email_task
from core.agents import EnterpriseAgentPool
from core.tasks import build_analysis_task
from database.task_history import task_history


def _append_row(file_path: str, row_data: list) -> None:
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
    except FileNotFoundError:
        wb = openpyxl.Workbook()
        sheet = wb.active
    sheet.append(row_data)
    wb.save(file_path)


@celery_app.task(name="workers.process_and_analyze_excel", bind=True, max_retries=3)
def process_and_analyze_excel(self, input_path: str, output_path: str, notify_email: str | None = None) -> dict:
    """
    Loads a CSV/Excel file, asks the Data Analyst agent for narrative
    insights (via its dataframe_summary tool), writes results to
    output_path, and optionally emails a summary.
    """
    import asyncio
    task_id = self.request.id
    
    # Record task start in Postgres (run async in sync context)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Create task record
        loop.run_until_complete(task_history.create_task(
            task_id, 
            "data_analysis",
            {"input_path": input_path, "output_path": output_path, "notify_email": notify_email}
        ))
        
        # Update status to started
        loop.run_until_complete(task_history.update_task_status(task_id, "started"))
        
        if input_path.lower().endswith(".csv"):
            df = pd.read_csv(input_path)
        else:
            df = pd.read_excel(input_path)

        pool = EnterpriseAgentPool()
        agent = pool.get_data_automation_agent()
        task = build_analysis_task(agent, input_path)
        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        insights = str(crew.kickoff())

        _append_row(output_path, ["Rows", len(df)])
        _append_row(output_path, ["Columns", ", ".join(str(c) for c in df.columns)])
        _append_row(output_path, ["AI Insights", insights])

        if notify_email:
            send_email_task.delay(
                notify_email,
                "Your data analysis is ready",
                f"Analysis complete for {input_path}.\n\nInsights:\n{insights}",
            )

        result = {"status": "complete", "rows": len(df), "insights": insights, "output_path": output_path}
        
        # Update task with result
        loop.run_until_complete(task_history.update_task_result(task_id, result))
        
        return result

    except Exception as exc:
        # Update task with error
        loop.run_until_complete(task_history.update_task_status(task_id, "failed", str(exc)))
        raise self.retry(exc=exc, countdown=10)
