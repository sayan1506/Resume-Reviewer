import re

import numpy as np
import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Resume
from langchain_core.prompts import ChatPromptTemplate
from ai.router import invoke_with_fallback
from services.pinecone_service import create_embedding, create_embeddings_batch
from schemas.ai_schema import JobMatchResponse, JobMatchItem, JobMatchAnalysisResult


REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
REQUEST_TIMEOUT = 10
POOL_CAP = 50          # max jobs fetched across all sources before ranking
TOP_K = 6              # jobs ranked + explained + returned
RESUME_CHARS = 2000    # truncate resume for embedding/LLM input
JOB_DESC_CHARS = 600   # truncate each job description

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", text or "")).strip()


def _fetch_remotive(query) -> list[dict]:
    params = {"limit": 30}
    if query and query.strip():
        params["search"] = query.strip()
    resp = requests.get(REMOTIVE_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [
        {
            "title": j.get("title", "").strip(),
            "company": (j.get("company_name") or "Unknown").strip(),
            "url": j.get("url", ""),
            "description": _strip_html(j.get("description", "")),
            "source": "Remotive",
        }
        for j in jobs
        if j.get("title") and j.get("url")
    ]


def _fetch_arbeitnow(query) -> list[dict]:
    resp = requests.get(ARBEITNOW_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    jobs = resp.json().get("data", [])
    results = [
        {
            "title": j.get("title", "").strip(),
            "company": (j.get("company_name") or "Unknown").strip(),
            "url": j.get("url", ""),
            "description": _strip_html(j.get("description", "")),
            "source": "Arbeitnow",
        }
        for j in jobs
        if j.get("title") and j.get("url")
    ]
    # Arbeitnow has no server-side search; do a light client-side keyword filter.
    if query and query.strip():
        q = query.strip().lower()
        filtered = [r for r in results if q in r["title"].lower() or q in r["description"].lower()]
        # Fall back to unfiltered if the filter is too aggressive — embedding ranking handles relevance.
        results = filtered if filtered else results
    return results


def _gather_jobs(query) -> list[dict]:
    """Fetch from both sources; one failing source must not sink the request."""
    pool: list[dict] = []
    for fetcher in (_fetch_remotive, _fetch_arbeitnow):
        try:
            pool.extend(fetcher(query))
        except Exception as e:
            print(f"[WARNING] job source {fetcher.__name__} failed: {e}")
    # De-duplicate by URL.
    seen = set()
    deduped = []
    for job in pool:
        if job["url"] in seen:
            continue
        seen.add(job["url"])
        deduped.append(job)
    return deduped[:POOL_CAP]


def _rank_jobs(resume_text: str, jobs: list[dict]) -> list[dict]:
    """Cosine-rank jobs against the resume; return the TOP_K most similar."""
    job_texts = [f"{j['title']}. {j['description'][:JOB_DESC_CHARS]}" for j in jobs]

    resume_vec = np.asarray(create_embedding(resume_text[:RESUME_CHARS]), dtype=float)
    job_vecs = np.asarray(create_embeddings_batch(job_texts), dtype=float)

    resume_norm = resume_vec / (np.linalg.norm(resume_vec) + 1e-10)
    job_norms = job_vecs / (np.linalg.norm(job_vecs, axis=1, keepdims=True) + 1e-10)
    sims = job_norms @ resume_norm

    top_idx = np.argsort(sims)[::-1][:TOP_K]
    return [jobs[i] for i in top_idx]


_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
You are a career advisor. A candidate's resume is below, followed by a numbered
list of job postings that were pre-selected as potentially relevant.

For EACH job (referenced by its index number), assess how well THIS candidate's
resume fits THAT job. Return one analysis per job with:
- "index": the job's index number (exactly as given).
- "matchPct": 0-100, how strong the fit is for this candidate.
- "whyFit": one or two sentences on why the candidate fits (or doesn't).
- "skillGaps": specific skills/requirements the candidate appears to be missing
  for this role (empty list if none).

Resume:
{resume}

Jobs:
{jobs}
"""
)


def job_match_service(resume_id: int, user_id: int, query, model_choice: str, db: Session) -> JobMatchResponse:

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    pool = _gather_jobs(query)
    if not pool:
        raise HTTPException(
            status_code=503,
            detail="Job sources are currently unavailable. Please try again shortly.",
        )

    top_jobs = _rank_jobs(resume.parsed_text, pool)

    jobs_block = "\n\n".join(
        f"[{i}] {j['title']} at {j['company']}\n{j['description'][:JOB_DESC_CHARS]}"
        for i, j in enumerate(top_jobs)
    )
    inputs = {"resume": resume.parsed_text[:RESUME_CHARS], "jobs": jobs_block}

    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: _ANALYSIS_PROMPT | llm.with_structured_output(JobMatchAnalysisResult),
        inputs,
    )
    raw = invoke_result.result

    analysis_by_index = {a.index: a for a in raw.analyses}

    items: list[JobMatchItem] = []
    for i, job in enumerate(top_jobs):
        analysis = analysis_by_index.get(i)
        items.append(JobMatchItem(
            title=job["title"],
            company=job["company"],
            url=job["url"],
            source=job["source"],
            matchPct=analysis.matchPct if analysis else 0,
            whyFit=analysis.whyFit if analysis else "No analysis available for this role.",
            skillGaps=analysis.skillGaps if analysis else [],
        ))

    items.sort(key=lambda x: x.matchPct, reverse=True)

    return JobMatchResponse(
        jobs=items,
        model_used=invoke_result.model_used,
        fallback_warning=invoke_result.fallback_warning,
    )
