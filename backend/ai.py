from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set in your .env file!")

client = Groq(api_key=api_key)
MODEL = "llama-3.3-70b-versatile"


def _chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


def generate_question(company: str, topic: str, difficulty: str) -> str:
    prompt = f"""You are a senior software engineer at {company} conducting a technical interview.

Generate ONE DSA interview question.
- Topic: {topic}
- Difficulty: {difficulty}
- Style it for {company} (Google = elegant algorithms, Amazon = practical/scalable, Microsoft = clear problem solving, Atlassian = collaborative/systems, Adobe = creative/efficient)

Return ONLY the problem statement. Include:
- Clear problem description
- Input/output format
- 2 example cases with explanation

No solution, no hints, no preamble."""

    try:
        return _chat(prompt)
    except Exception as e:
        raise RuntimeError(f"Groq API error: {str(e)}")


def evaluate_answer(question: str, answer: str, topic: str, difficulty: str) -> dict:
    prompt = f"""You are an expert DSA interviewer at a top tech company. Evaluate this candidate's approach explanation.

QUESTION:
{question}

CANDIDATE'S EXPLANATION:
{answer}

Evaluate strictly and fairly across all dimensions. Return ONLY a valid JSON object, no markdown, no backticks:
{{
  "score": <integer 0-100>,
  "correctness": "<Excellent|Good|Partial|Incorrect>",
  "correctness_explanation": "<2-3 sentences: is their approach logically correct? would it solve all cases?>",
  "time_complexity": "<what they stated or what their approach implies, e.g. O(n log n)>",
  "time_complexity_assessment": "<Excellent|Good|Can Improve|Not Mentioned>",
  "space_complexity": "<what they stated or what their approach implies>",
  "space_complexity_assessment": "<Excellent|Good|Can Improve|Not Mentioned>",
  "edge_cases_handled": "<Good|Partial|Not Addressed>",
  "edge_cases_explanation": "<which edge cases they mentioned or missed>",
  "communication": "<Clear|Adequate|Needs Improvement>",
  "communication_explanation": "<was the explanation structured and easy to follow?>",
  "optimal_solution": "<explain the optimal approach clearly with time and space complexity>",
  "overall_feedback": "<3-4 sentences of honest, constructive feedback an interviewer would give>",
  "follow_up": "<one natural follow-up question an interviewer would ask next>"
}}"""

    try:
        text = _chat(prompt)
        if "```" in text:
            for part in text.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("{"):
                    text = part
                    break
        return json.loads(text)

    except json.JSONDecodeError:
        return {
            "score": 0,
            "correctness": "Error",
            "correctness_explanation": "Could not parse AI response. Please try again.",
            "time_complexity": "N/A",
            "time_complexity_assessment": "N/A",
            "space_complexity": "N/A",
            "space_complexity_assessment": "N/A",
            "edge_cases_handled": "N/A",
            "edge_cases_explanation": "N/A",
            "communication": "N/A",
            "communication_explanation": "N/A",
            "optimal_solution": "N/A",
            "overall_feedback": "Evaluation failed. Please try submitting again.",
            "follow_up": "N/A"
        }
    except Exception as e:
        raise RuntimeError(f"Groq API error: {str(e)}")


def evaluate_followup(question: str, answer: str) -> str:
    prompt = f"""A DSA interviewer asked this follow-up:
{question}

The candidate answered:
{answer}

Give brief, direct feedback in 2-3 sentences. Be honest — what's right, what's missing, what's the key insight."""
    try:
        return _chat(prompt)
    except Exception as e:
        raise RuntimeError(f"Groq API error: {str(e)}")


def get_weak_topic(interviews: list) -> str:
    if not interviews:
        return "N/A"
    topic_scores, topic_counts = {}, {}
    for iv in interviews:
        t = iv.get("topic", "Unknown")
        s = iv.get("score") or 0
        topic_scores[t] = topic_scores.get(t, 0) + s
        topic_counts[t] = topic_counts.get(t, 0) + 1
    averages = {t: topic_scores[t] / topic_counts[t] for t in topic_scores}
    return min(averages, key=averages.get)
