import os
import re
import time
from datetime import datetime, timezone
from curl_cffi import requests
from google import genai

# ──────────────────────────────────────────────
# Configuration & Secrets (set via GitHub Actions secrets)
# ──────────────────────────────────────────────
USERNAME = os.getenv("LC_USERNAME")
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Choose "cpp" or "java"
TARGET_LANG = os.getenv("TARGET_LANG", "cpp")
MAX_ATTEMPTS = 3

GRAPHQL_URL = "https://leetcode.com/graphql"


# ──────────────────────────────────────────────
# Session
# ──────────────────────────────────────────────
def get_session():
    """Creates an authenticated LeetCode session using browser impersonation."""
    session = requests.Session(impersonate="chrome120")
    session.headers.update({
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/",
        "x-csrftoken": CSRF_TOKEN or "",
    })
    session.cookies.set("LEETCODE_SESSION", LEETCODE_SESSION, domain=".leetcode.com")
    session.cookies.set("csrftoken", CSRF_TOKEN, domain=".leetcode.com")
    return session


# ──────────────────────────────────────────────
# LeetCode GraphQL helpers
# ──────────────────────────────────────────────
def get_daily_slug(session) -> dict:
    """Gets today's Daily Challenge metadata."""
    query = """
    query questionOfToday {
      activeDailyCodingChallengeQuestion {
        date
        link
        userStatus
        question {
          questionId
          title
          titleSlug
          difficulty
        }
      }
    }
    """
    resp = session.post(GRAPHQL_URL, json={"query": query})
    return resp.json()["data"]["activeDailyCodingChallengeQuestion"]


def get_problem_details(session, title_slug: str) -> dict:
    """Fetches full HTML description and language starter templates."""
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        title
        content
        difficulty
        exampleTestcases
        codeSnippets {
          lang
          langSlug
          code
        }
      }
    }
    """
    resp = session.post(GRAPHQL_URL, json={
        "query": query,
        "variables": {"titleSlug": title_slug}
    })
    return resp.json()["data"]["question"]


# ──────────────────────────────────────────────
# Gemini AI solver
# ──────────────────────────────────────────────
def strip_markdown_fences(text: str) -> str:
    """Removes ```cpp / ```java fences from LLM output."""
    text = text.strip()
    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def generate_solution(problem: dict, lang_slug: str, error_feedback: str = "") -> str:
    """Calls Gemini to generate or fix a C++ / Java solution."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Extract the exact starter template for C++ or Java
    starter_code = next(
        (s["code"] for s in problem["codeSnippets"] if s["langSlug"] == lang_slug),
        ""
    )

    prompt = f"""You are a Grandmaster competitive programmer. Solve the following LeetCode problem in {lang_slug.upper()}.

Problem Title: {problem['title']} ({problem['difficulty']})
Problem Description (HTML):
{problem['content']}

Starter Code Template (DO NOT change the class or method signature):
{starter_code}

Requirements:
1. Write an optimal solution that passes all time and space complexity constraints.
2. Output ONLY the raw, compilable {lang_slug.upper()} code. Do NOT include explanations or markdown formatting outside the code.
3. Keep everything inside the required `class Solution` structure provided in the starter template.
"""
    if error_feedback:
        prompt += f"\nYour previous submission failed with the following judge feedback. Fix the bug or optimize the algorithm:\n{error_feedback}\n"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return strip_markdown_fences(response.text)


# ──────────────────────────────────────────────
# LeetCode submit + poll
# ──────────────────────────────────────────────
def submit_and_poll(session, title_slug: str, question_id: str, lang_slug: str, code: str) -> dict:
    """Submits code to LeetCode and polls until the judge finishes grading."""
    submit_url = f"https://leetcode.com/problems/{title_slug}/submit/"
    session.headers.update({"Referer": f"https://leetcode.com/problems/{title_slug}/"})

    payload = {
        "lang": lang_slug,
        "question_id": str(question_id),
        "typed_code": code,
    }
    resp = session.post(submit_url, json=payload)
    if resp.status_code != 200 or "submission_id" not in resp.json():
        raise RuntimeError(f"Submission rejected ({resp.status_code}): {resp.text}")

    submission_id = resp.json()["submission_id"]
    print(f"  Submitted! Polling Submission ID: {submission_id}...")

    # Poll /submissions/detail/<id>/check/ every 3 seconds
    check_url = f"https://leetcode.com/submissions/detail/{submission_id}/check/"
    for _ in range(20):
        time.sleep(3)
        check_resp = session.get(check_url).json()
        if check_resp.get("state") == "SUCCESS":
            return check_resp

    return {"status_msg": "Polling Timeout"}


# ──────────────────────────────────────────────
# Fallback — Two Sum (guaranteed AC to save streak)
# ──────────────────────────────────────────────
def submit_fallback_two_sum(session):
    """Guaranteed fallback if the AI fails all attempts on the daily problem."""
    cpp_code = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for (int i = 0; i < nums.size(); i++) {
            if (mp.count(target - nums[i])) return {mp[target - nums[i]], i};
            mp[nums[i]] = i;
        }
        return {};
    }
};
"""
    submit_and_poll(session, "two-sum", "1", "cpp", cpp_code)


# ──────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────
def notify(msg: str):
    """Prints to stdout (visible in Actions logs) and optionally pings Discord."""
    print(msg)
    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})


# ──────────────────────────────────────────────
# Main entry-point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    client = get_session()
    daily = get_daily_slug(client)

    # userStatus == "Finish" means today's daily coin is already earned
    if daily.get("userStatus") == "Finish":
        print("✅ Today's Daily Challenge is already completed!")
        exit(0)

    slug = daily["question"]["titleSlug"]
    problem = get_problem_details(client, slug)
    print(f"🎯 Solving Daily: {problem['title']} ({problem['difficulty']}) in {TARGET_LANG}...")

    feedback = ""
    solved = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- Attempt {attempt}/{MAX_ATTEMPTS} ---")
        code = generate_solution(problem, TARGET_LANG, feedback)
        result = submit_and_poll(client, slug, problem["questionId"], TARGET_LANG, code)
        status = result.get("status_msg", "Unknown Error")

        if status == "Accepted":
            runtime = result.get("status_runtime", "N/A")
            percentile = round(result.get("runtime_percentile", 0), 1)
            notify(
                f"✅ **Daily Challenge Solved!**\n"
                f"**Problem:** {problem['title']} ({problem['difficulty']})\n"
                f"**Language:** `{TARGET_LANG}` | **Attempt:** {attempt}\n"
                f"**Runtime:** {runtime} (Beats {percentile}%)"
            )
            solved = True
            break
        else:
            # Build error feedback for the next LLM retry
            feedback = (
                f"Status: {status}\n"
                f"Compile Error: {result.get('full_compile_error', 'None')}\n"
                f"Runtime Error: {result.get('full_runtime_error', 'None')}\n"
                f"Last Testcase: {result.get('last_testcase', 'N/A')}\n"
                f"Your Output: {result.get('code_output', 'N/A')}\n"
                f"Expected Output: {result.get('expected_output', 'N/A')}\n"
                f"Previous Code:\n{code}"
            )
            print(f"  ❌ Attempt {attempt} failed: {status}. Waiting 12s for rate-limit...")
            time.sleep(12)  # LeetCode enforces a ~10s cooldown between submissions

    if not solved:
        notify(
            f"⚠️ AI failed to solve **{problem['title']}** after {MAX_ATTEMPTS} tries. "
            f"Submitting Two Sum fallback to save streak."
        )
        submit_fallback_two_sum(client)
