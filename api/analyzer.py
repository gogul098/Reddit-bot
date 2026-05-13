import os
import json
from groq import Groq

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def format_comments(comments_data):
    formatted_comments = []
    for c in comments_data:
        c_id = c.get('id', 'unknown') if isinstance(c, dict) else getattr(c, 'id', 'unknown')
        c_author = c.get('author', 'unknown') if isinstance(c, dict) else getattr(c, 'author', 'unknown')
        c_body = c.get('body', '') if isinstance(c, dict) else getattr(c, 'body', '')
        formatted_comments.append(f"[{c_id}] {c_author}: {c_body}")
    return "\n".join(formatted_comments)

def analyze_summary_and_toxicity_with_groq(post_title: str, comments_data: list) -> dict:
    client = get_groq_client()
    if not client:
        return {"error": "GROQ_API_KEY is missing.", "summary": "N/A", "toxicity_level": "Unknown"}

    comments_string = format_comments(comments_data)
    
    system_prompt = """You are an expert AI Reddit moderator.
Your task is to summarize the thread and detect the overall toxicity level in the content.
You MUST output your response in JSON format with the following keys:
- "summary": A brief string summarizing the thread discussion.
- "toxicity_level": A string representing the toxicity level (e.g., "Low", "Medium", "High").
"""
    user_prompt = f"Title: {post_title}\n\nComments:\n{comments_string}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "summary": "Error", "toxicity_level": "Error"}


def analyze_escalation_with_groq(post_title: str, comments_data: list) -> dict:
    client = get_groq_client()
    if not client:
        return {"error": "GROQ_API_KEY is missing.", "escalation_detected": False, "reasoning": "N/A"}

    comments_string = format_comments(comments_data)
    
    system_prompt = """You are an expert AI Reddit moderator.
Your task is to analyze a series of comments to find whether there is a fight between the users and if it is turning abusive and personal.
You MUST output your response in JSON format with the following keys:
- "escalation_detected": A boolean indicating if a fight or personal abuse is detected.
- "reasoning": A brief string explaining why escalation was or wasn't detected.
"""
    user_prompt = f"Title: {post_title}\n\nComments:\n{comments_string}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "escalation_detected": False, "reasoning": "Error occurred"}
