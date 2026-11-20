
import json

from langchain_ollama import ChatOllama

from app.schemas.candidate import CandidateProfile


llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    format="json"
)


def extract_candidate_profile(
    resume_text: str
) -> CandidateProfile:

    prompt = f"""
You are an expert resume information extraction system.

Extract information from the resume below.

Return ONLY valid JSON with these fields:

{{
    "name": null,
    "email": null,
    "phone": null,
    "education": [],
    "skills": [],
    "experience_years": 0,
    "preferred_roles": [],
    "preferred_locations": []
}}

Rules:
1. Only extract information supported by the resume.
2. Never invent skills or qualifications.
3. Use an empty list when information is unavailable.
4. Use null for unavailable name, email or phone.
5. Experience must be a non-negative number.
6. Do not infer job preferences from skills.
   Leave preferred_roles and preferred_locations empty
   unless explicitly stated.
7. Return valid JSON only.

RESUME:
{resume_text}
"""

    response = llm.invoke(prompt)

    try:
        raw_result = json.loads(response.content)

        profile = CandidateProfile.model_validate(
            raw_result
        )

        return profile

    except Exception as exc:
        raise ValueError(
            f"Could not extract a valid candidate profile: {exc}"
        ) from exc
