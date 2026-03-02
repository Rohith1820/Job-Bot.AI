import anthropic, re, json

client = anthropic.Anthropic()

def tailor_resume(base_resume: str, jd: str, role: str, company: str, 
                  candidate_name: str, email: str, phone: str) -> dict:
    """Tailor resume for a specific JD using Claude. Returns tailored text + score."""
    
    prompt = f"""You are an expert ATS resume optimizer.

CANDIDATE: {candidate_name}
EMAIL: {email}
PHONE: {phone}

BASE RESUME:
{base_resume}

TARGET ROLE: {role} at {company}

JOB DESCRIPTION:
{jd}

Instructions:
1. Rewrite bullet points to mirror JD keywords exactly
2. Reorder skills to match what the JD prioritizes
3. Keep the candidate's email ({email}) and phone ({phone}) in the header — do NOT change them
4. Keep all facts truthful — never fabricate experience
5. Make it ATS-friendly with proper keywords
6. At the very last line output: MATCH_SCORE: [0-100]

Return only the tailored resume + score line."""

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = message.content[0].text
    score_match = re.search(r'MATCH_SCORE:\s*(\d+)', text)
    score = int(score_match.group(1)) if score_match else 75
    resume_text = re.sub(r'MATCH_SCORE:\s*\d+', '', text).strip()
    
    return {"tailored": resume_text, "score": score}
