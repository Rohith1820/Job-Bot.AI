from weasyprint import HTML
import boto3, uuid, os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
)

def resume_to_html(resume_text: str) -> str:
    lines = resume_text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br>")
        elif line.isupper() or line.endswith(":"):
            html_lines.append(f"<h2>{line}</h2>")
        elif line.startswith("-") or line.startswith("•"):
            html_lines.append(f"<li>{line[1:].strip()}</li>")
        else:
            html_lines.append(f"<p>{line}</p>")
    
    return f"""
    <html><head><style>
        body {{ font-family: Arial, sans-serif; font-size: 11px; margin: 40px; color: #222; }}
        h1 {{ font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #6c63ff; }}
        h2 {{ font-size: 13px; color: #6c63ff; border-bottom: 1px solid #eee; margin-top: 14px; }}
        p, li {{ margin: 2px 0; line-height: 1.5; }}
        ul {{ padding-left: 18px; }}
    </style></head>
    <body>{''.join(html_lines)}</body></html>"""

def generate_and_upload_pdf(resume_text: str, filename: str = None) -> str:
    """Generate PDF from resume text, upload to S3, return public URL."""
    if not filename:
        filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
    
    html = resume_to_html(resume_text)
    pdf_bytes = HTML(string=html).write_pdf()
    
    s3.put_object(
        Bucket=os.getenv("S3_BUCKET"),
        Key=f"resumes/{filename}",
        Body=pdf_bytes,
        ContentType="application/pdf",
        ACL="public-read"
    )
    
    return f"https://{os.getenv('S3_BUCKET')}.s3.amazonaws.com/resumes/{filename}"
