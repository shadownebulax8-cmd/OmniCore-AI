import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from crewai import Crew

from pipeline.validation import (
    SupportQuestionRequest, SupportAnswerResponse,
    KnowledgeDocRequest, KnowledgeSearchRequest, KnowledgeSearchResponse,
    BulkImportResponse,
    ContentBriefRequest, ContentResponse,
    AnalysisTaskResponse, AnalysisStatusResponse,
    DailyMetricsResponse, LatencyStatsResponse, TrendsResponse,
)
from api.rate_limiter import rate_limit_dependency
from config.settings import settings
from core.agents import EnterpriseAgentPool
from core.tasks import build_support_task, build_content_task
from memory.vector_store import KnowledgeBaseStore
from memory.semantic_cache import SemanticCache
from memory.conversation_context import conversation_context
from workers.sheet_worker import process_and_analyze_excel
from workers.email_worker import send_email_task
from workers.celery_app import celery_app
from analytics.metrics import analytics
from database.task_history import task_history

router = APIRouter(dependencies=[Depends(rate_limit_dependency)])

UPLOAD_DIR = Path("data/uploads")
OUTPUT_DIR = Path("data/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/health")
async def health():
    return {"status": "ok"}


# ---------- Support Bot ----------

@router.post("/support/ask", response_model=SupportAnswerResponse)
async def ask_support(payload: SupportQuestionRequest):
    import time
    start_time = time.time()
    
    # Handle session creation/retrieval
    session_id = payload.session_id
    if not session_id or not conversation_context.session_exists(session_id):
        session_id = conversation_context.create_session()
    
    # Get conversation context if available
    context_history = conversation_context.get_formatted_context(session_id)
    
    cache = SemanticCache()
    cached = cache.get(payload.question)
    
    if cached:
        # Track cache hit
        analytics.track_agent_request("support", success=True, 
                                     latency_ms=(time.time() - start_time) * 1000, 
                                     cache_hit=True)
        analytics.track_popular_question(payload.question)
        
        # Still add to conversation history for context
        conversation_context.add_exchange(session_id, payload.question, cached, False)
        
        return SupportAnswerResponse(answer=cached, escalated=False, source="cache", session_id=session_id)

    # Build question with context
    question_with_context = payload.question
    if context_history:
        question_with_context = f"Previous conversation:\n{context_history}\n\nCurrent question: {payload.question}"

    pool = EnterpriseAgentPool()
    agent = pool.get_customer_support_agent()
    task = build_support_task(agent, question_with_context)
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    answer = str(crew.kickoff())

    escalated = answer.strip().upper().startswith("ESCALATE")
    latency_ms = (time.time() - start_time) * 1000
    
    if not escalated:
        cache.set(payload.question, answer)
        analytics.track_agent_request("support", success=True, 
                                     latency_ms=latency_ms, cache_hit=False)
    else:
        analytics.track_agent_request("support", success=False, 
                                     latency_ms=latency_ms, cache_hit=False)
        analytics.track_escalation(payload.question, payload.customer_email)
        if settings.SUPPORT_ESCALATION_EMAIL:
            send_email_task.delay(
                settings.SUPPORT_ESCALATION_EMAIL,
                "Support escalation: unanswered customer question",
                f"Question: {payload.question}\n"
                f"Customer email: {payload.customer_email or 'not provided'}\n"
                f"Agent note: {answer}",
            )
    
    analytics.track_popular_question(payload.question)
    
    # Add to conversation history
    conversation_context.add_exchange(session_id, payload.question, answer, escalated)

    return SupportAnswerResponse(answer=answer, escalated=escalated, source="agent", session_id=session_id)


@router.post("/support/knowledge")
async def add_knowledge(payload: KnowledgeDocRequest):
    store = KnowledgeBaseStore()
    doc_id = store.add_document(payload.text, payload.metadata)
    return {"status": "added", "doc_id": doc_id}


@router.post("/support/knowledge/bulk", response_model=BulkImportResponse)
async def bulk_import_knowledge(file: UploadFile = File(...)):
    """Bulk import knowledge base documents from CSV or JSON file."""
    import json
    import csv
    import io
    
    store = KnowledgeBaseStore()
    imported_count = 0
    failed_count = 0
    errors = []
    
    try:
        content = await file.read()
        
        if file.filename.lower().endswith('.json'):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    documents = data
                elif isinstance(data, dict) and 'documents' in data:
                    documents = data['documents']
                else:
                    raise ValueError("Invalid JSON format")
                
                for doc in documents:
                    try:
                        text = doc.get('text') or doc.get('content')
                        if not text or len(text) < 10:
                            errors.append(f"Document missing valid text: {doc}")
                            failed_count += 1
                            continue
                        
                        metadata = doc.get('metadata', {})
                        store.add_document(text, metadata)
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Failed to import document: {str(e)}")
                        failed_count += 1
                        
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON file: {str(e)}")
                failed_count = 1
                
        elif file.filename.lower().endswith('.csv'):
            try:
                csv_content = content.decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                
                for row in csv_reader:
                    try:
                        text = row.get('text') or row.get('content') or row.get('question')
                        if not text or len(text) < 10:
                            errors.append(f"Row missing valid text: {row}")
                            failed_count += 1
                            continue
                        
                        # Build metadata from other columns
                        metadata = {k: v for k, v in row.items() 
                                  if k not in ['text', 'content', 'question'] and v}
                        
                        store.add_document(text, metadata)
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Failed to import row: {str(e)}")
                        failed_count += 1
                        
            except Exception as e:
                errors.append(f"Invalid CSV file: {str(e)}")
                failed_count = 1
        else:
            errors.append("Unsupported file format. Use .json or .csv")
            failed_count = 1
            
    except Exception as e:
        errors.append(f"File processing error: {str(e)}")
        failed_count = 1
    
    return BulkImportResponse(
        status="completed",
        imported_count=imported_count,
        failed_count=failed_count,
        errors=errors
    )


@router.post("/support/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(payload: KnowledgeSearchRequest):
    """Search the knowledge base directly without going through the agent."""
    store = KnowledgeBaseStore()
    results = store.search(payload.query, n_results=payload.n_results)
    
    formatted_results = []
    if results and 'documents' in results and results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            formatted_results.append({
                "content": doc,
                "metadata": results.get('metadatas', [[]])[0][i] if results.get('metadatas') else {},
                "distance": results.get('distances', [[]])[0][i] if results.get('distances') else None
            })
    
    return KnowledgeSearchResponse(query=payload.query, results=formatted_results)


@router.post("/support/session")
async def create_session():
    """Create a new conversation session."""
    session_id = conversation_context.create_session()
    return {"session_id": session_id}


@router.get("/support/session/{session_id}")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    if not conversation_context.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": conversation_context.get_context(session_id)}


@router.delete("/support/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    if not conversation_context.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    conversation_context.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


# ---------- Content Generator ----------

@router.post("/content/generate", response_model=ContentResponse)
async def generate_content(payload: ContentBriefRequest):
    import time
    start_time = time.time()
    
    pool = EnterpriseAgentPool()
    agent = pool.get_content_generation_agent()
    task = build_content_task(agent, payload.model_dump())
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    content = str(crew.kickoff())
    
    analytics.track_agent_request("content", success=True, 
                                 latency_ms=(time.time() - start_time) * 1000)
    
    return ContentResponse(content=content)


# ---------- Data Analyst ----------

@router.post("/analyst/upload", response_model=AnalysisTaskResponse)
async def upload_for_analysis(file: UploadFile = File(...), notify_email: str | None = None):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, .xls files are supported")

    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    output_path = OUTPUT_DIR / f"{file_id}_report.xlsx"

    with input_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    task = process_and_analyze_excel.delay(str(input_path), str(output_path), notify_email)
    
    # Create task record in Postgres
    await task_history.create_task(
        task.id,
        "data_analysis",
        {"input_path": str(input_path), "output_path": str(output_path), "notify_email": notify_email}
    )
    
    return AnalysisTaskResponse(task_id=task.id, status="queued")


@router.get("/analyst/status/{task_id}", response_model=AnalysisStatusResponse)
async def analysis_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    
    # Try to get additional data from Postgres
    task_record = await task_history.get_task(task_id)
    
    return AnalysisStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() and result.successful() else None,
    )


@router.get("/tasks/history")
async def get_task_history(limit: int = 50, status: str | None = None, task_type: str | None = None):
    """Get task history with optional filters."""
    if status:
        tasks = await task_history.get_tasks_by_status(status, limit)
    elif task_type:
        tasks = await task_history.get_tasks_by_type(task_type, limit)
    else:
        tasks = await task_history.get_recent_tasks(limit)
    
    return {"tasks": tasks, "count": len(tasks)}


@router.get("/tasks/statistics")
async def get_task_statistics():
    """Get task statistics."""
    return await task_history.get_task_statistics()


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get detailed information about a specific task."""
    task = await task_history.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------- Analytics ----------

@router.get("/analytics/metrics", response_model=DailyMetricsResponse)
async def get_analytics_metrics(date: str | None = None):
    """Get daily metrics for agent usage and performance."""
    return analytics.get_daily_metrics(date)


@router.get("/analytics/latency/{agent_type}", response_model=LatencyStatsResponse)
async def get_latency_stats(agent_type: str, date: str | None = None):
    """Get latency statistics for a specific agent."""
    if agent_type not in ["support", "content", "analyst"]:
        raise HTTPException(status_code=400, detail="Invalid agent type")
    return analytics.get_latency_stats(agent_type, date)


@router.get("/analytics/escalations")
async def get_escalations(date: str | None = None, limit: int = 50):
    """Get recent escalated support questions."""
    return analytics.get_escalations(date, limit)


@router.get("/analytics/popular-questions")
async def get_popular_questions(date: str | None = None, limit: int = 20):
    """Get most frequently asked questions."""
    return analytics.get_popular_questions(date, limit)


@router.get("/analytics/trends", response_model=TrendsResponse)
async def get_analytics_trends(days: int = 7):
    """Get usage trends over multiple days."""
    if days > 30:
        raise HTTPException(status_code=400, detail="Maximum 30 days")
    return analytics.get_trends(days)
