import sendgrid
from sendgrid.helpers.mail import Mail
import os

sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

def send_application_confirmation(
    to_email: str, candidate_name: str,
    company: str, role: str, pdf_url: str, match_score: int
):
    """Send email to client confirming their application was submitted."""
    
    html = f"""
    <div style="font-family:Arial;max-width:600px;margin:auto;padding:30px">
      <div style="background:linear-gradient(135deg,#6c63ff,#3b82f6);padding:20px;border-radius:12px;color:white;text-align:center">
        <h1 style="margin:0">✅ Application Submitted!</h1>
      </div>
      <div style="padding:24px;background:#f9f9f9;border-radius:12px;margin-top:16px">
        <p>Hi <strong>{candidate_name}</strong>,</p>
        <p>Your JobBot AI has successfully submitted an application on your behalf:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr><td style="padding:8px;color:#555">Company</td><td><strong>{company}</strong></td></tr>
          <tr><td style="padding:8px;color:#555">Role</td><td><strong>{role}</strong></td></tr>
          <tr><td style="padding:8px;color:#555">JD Match</td><td><strong style="color:#6c63ff">{match_score}%</strong></td></tr>
          <tr><td style="padding:8px;color:#555">Applied with</td><td><strong>{to_email}</strong></td></tr>
        </table>
        <a href="{pdf_url}" style="display:inline-block;background:#6c63ff;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold">
          📄 Download Tailored Resume
        </a>
        <p style="color:#999;font-size:12px;margin-top:20px">
          This application was submitted automatically by JobBot AI. 
          Watch your inbox ({to_email}) for a response from {company}.
        </p>
      </div>
    </div>"""

    message = Mail(
        from_email="bot@yourdomain.com",
        to_emails=to_email,
        subject=f"✅ JobBot Applied: {role} at {company}",
        html_content=html
    )
    sg.send(message)
