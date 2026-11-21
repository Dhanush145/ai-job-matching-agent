
import json

from langchain_ollama import ChatOllama

from app.schemas.candidate import CandidateProfile


# Initialize local Ollama LLM
llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    format="json"
)


def extract_candidate_profile(
    resume_text: str
) -> CandidateProfile:
    """
    Extract structured candidate information from resume text
    using the locally running Llama 3.1 model.

    Args:
        resume_text: Extracted text from the uploaded PDF.

    Returns:
        Validated CandidateProfile object.
    """

    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    prompt = f"""
You are an expert AI resume parsing and information extraction system.

Your task is to extract candidate information from the
provided resume and return structured JSON.

Return ONLY valid JSON using exactly this structure:

{{
    "name": null,
    "email": null,
    "phone": null,

    "education": [
        {{
            "institution": null,
            "degree": null,
            "field_of_study": null,
            "graduation_year": null,
            "cgpa": null
        }}
    ],

    "skills": [],

    "experience_years": 0,

    "preferred_roles": [],

    "preferred_locations": []
}}

EXTRACTION RULES:

1. Extract only information explicitly supported by the resume.

2. Never invent candidate information, skills,
   education or work experience.

3. NAME:
   Extract the candidate's full name.

4. EMAIL:
   Extract the candidate's email address.
   Return null if unavailable.

5. PHONE:
   Extract the candidate's phone number.
   Return null if unavailable.

6. EDUCATION:
   Extract every available educational qualification.
   Each education entry must be a JSON object containing:
   institution, degree, field_of_study,
   graduation_year and cgpa.
   Use null for unavailable fields.

7. SKILLS:
   Extract technical and relevant professional skills.
   Return a list of strings.
   Avoid duplicate skills.

8. EXPERIENCE:
   Calculate total professional work experience
   based on actual employment periods.
   Do not count academic projects as employment.
   Do not count overlapping employment periods twice.
   If no employment experience is mentioned, return 0.

9. PREFERRED ROLES:
   Extract only explicitly stated preferred job roles.
   Do not infer preferences from technical skills.

10. PREFERRED LOCATIONS:
    Extract only explicitly stated preferred locations.
    Do not infer locations from the institution address.

11. JSON:
    Return valid JSON only.
    Do not include Markdown code blocks.
    Do not include explanations outside JSON.

RESUME CONTENT:

{resume_text}
"""

    try:
        # Invoke local LLM
        response = llm.invoke(prompt)

        # Parse JSON response
        raw_result = json.loads(response.content)

        # Validate extracted information
        profile = CandidateProfile.model_validate(
            raw_result
        )

        return profile

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Ollama returned invalid JSON. "
            "Please try uploading the resume again."
        ) from exc

    except Exception as exc:
        raise ValueError(
            f"Could not extract a valid candidate profile: {exc}"
        ) from exc
