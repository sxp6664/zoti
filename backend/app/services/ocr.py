"""ID-document OCR.

Two providers behind one interface:
  - `textract`: AWS Textract (real, accurate; needs AWS credentials)
  - `mock`: returns canned fields so the whole flow runs with no AWS key

Switch via OCR_PROVIDER env var. The router doesn't know or care which is
active — that's the point of the seam.
"""
import re

from app.core.config import settings


def _parse_fields(lines: list[str]) -> dict:
    """Heuristic extraction of name/DOB/doc-number from raw OCR lines.
    Real IDs vary wildly; this is a pragmatic best-effort the UI lets the
    guest correct before submitting."""
    text = "\n".join(lines)
    out = {"full_name": None, "last_name": None, "dob": None, "doc_number": None}

    dob = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", text)
    if dob:
        out["dob"] = dob.group(1)

    docnum = re.search(r"\b([A-Z0-9]{6,12})\b", text)
    if docnum:
        out["doc_number"] = docnum.group(1)

    # crude name guess: first line that's mostly letters + spaces
    for ln in lines:
        if re.fullmatch(r"[A-Za-z ,.'-]{4,40}", ln.strip()):
            out["full_name"] = ln.strip().title()
            out["last_name"] = ln.strip().split()[-1].title()
            break
    return out


def extract_id_fields(image_bytes: bytes) -> dict:
    if settings.OCR_PROVIDER == "textract":
        import boto3  # imported lazily so the mock path needs no AWS deps

        client = boto3.client("textract", region_name=settings.AWS_REGION)
        resp = client.detect_document_text(Document={"Bytes": image_bytes})
        lines = [b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE"]
        return {"provider": "textract", **_parse_fields(lines)}

    # mock provider
    return {
        "provider": "mock",
        "full_name": "Jordan Avery Patel",
        "last_name": "Patel",
        "dob": "04/12/1998",
        "doc_number": "X1234567",
    }
