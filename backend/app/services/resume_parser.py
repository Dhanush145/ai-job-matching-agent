
import fitz


def extract_resume_text(file_bytes: bytes) -> str:
    """
    Extract text from an uploaded PDF resume.
    """

    try:
        document = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        extracted_pages = []

        for page in document:
            text = page.get_text("text")
            extracted_pages.append(text)

        document.close()

        resume_text = "\n".join(extracted_pages).strip()

        if not resume_text:
            raise ValueError(
                "No readable text found in PDF. "
                "The resume may be scanned."
            )

        return resume_text

    except fitz.FileDataError as exc:
        raise ValueError("Invalid PDF file.") from exc
