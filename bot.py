import os
import re
import sys
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
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Choose "cpp" or "java"
TARGET_LANG = os.getenv("TARGET_LANG", "cpp")
MAX_ATTEMPTS = 3

GRAPHQL_URL = "https://leetcode.com/graphql"


# ──────────────────────────────────────────────
# Session & Anti-Bot Protection
# ──────────────────────────────────────────────
BROWSER_PROFILES = ["chrome124", "chrome", "safari17_0", "chrome131"]


def get_session(impersonate_target: str = "chrome124") -> requests.Session:
    """Creates an authenticated LeetCode session with realistic browser headers."""
    session = requests.Session(impersonate=impersonate_target)
    csrf = CSRF_TOKEN or ""
    session.headers.update({
        "Content-Type": "application/json",
        "Origin": "https://leetcode.com",
        "Referer": "https://leetcode.com/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-csrftoken": csrf,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    if LEETCODE_SESSION:
        session.cookies.set("LEETCODE_SESSION", LEETCODE_SESSION, domain=".leetcode.com")
    if csrf:
        session.cookies.set("csrftoken", csrf, domain=".leetcode.com")
    return session


def sync_csrf(session: requests.Session) -> str:
    """Keeps x-csrftoken header and csrftoken cookie in sync to prevent 403 CSRF rejections."""
    token = session.cookies.get("csrftoken") or CSRF_TOKEN or ""
    if token:
        session.headers["x-csrftoken"] = token
        session.cookies.set("csrftoken", token, domain=".leetcode.com")
    return token


def check_auth(session: requests.Session) -> tuple[bool, str]:
    """Validates whether LEETCODE_SESSION is active and signed in."""
    query = """
    query globalData {
      userStatus {
        isSignedIn
        username
      }
    }
    """
    try:
        sync_csrf(session)
        resp = session.post(GRAPHQL_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("userStatus", {})
            return bool(data.get("isSignedIn", False)), str(data.get("username", ""))
    except Exception as e:
        print(f"  ⚠️ Auth check error: {e}")
    return False, ""


def warm_up_problem_page(session: requests.Session, title_slug: str):
    """Visits the problem page to populate session cookies and establish normal navigation history."""
    url = f"https://leetcode.com/problems/{title_slug}/"
    try:
        session.get(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
            },
            timeout=15,
        )
        sync_csrf(session)
    except Exception as e:
        print(f"  ⚠️ Problem page warm-up warning: {e}")


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
    sync_csrf(session)
    resp = session.post(GRAPHQL_URL, json={"query": query}, timeout=15)
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
    sync_csrf(session)
    resp = session.post(GRAPHQL_URL, json={
        "query": query,
        "variables": {"titleSlug": title_slug}
    }, timeout=15)
    return resp.json()["data"]["question"]


# ──────────────────────────────────────────────
# Gemini AI solver
# ──────────────────────────────────────────────
def strip_markdown_fences(text: str) -> str:
    """Removes ```cpp / ```java fences from LLM output."""
    text = text.strip()
    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def call_nvidia_ai(prompt: str) -> str:
    """Calls NVIDIA NIM API with dynamic model discovery as secondary AI fallback."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    # 1. Dynamically query available active models on this NVIDIA account
    active_models = []
    try:
        resp = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            all_ids = [m["id"] for m in data if "id" in m]
            # Prioritize top coding / reasoning models first
            coder_models = [m for m in all_ids if "coder" in m.lower() or "deepseek" in m.lower()]
            llama_models = [m for m in all_ids if "llama" in m.lower() and "instruct" in m.lower()]
            other_instruct = [m for m in all_ids if "instruct" in m.lower()]
            active_models = coder_models + llama_models + other_instruct
            # Remove duplicates preserving order
            seen = set()
            active_models = [m for m in active_models if not (m in seen or seen.add(m))]
            print(f"  📋 Found {len(active_models)} compatible active NVIDIA models.")
    except Exception as e:
        print(f"  ⚠️ Could not fetch NVIDIA models list: {e}")

    # Fallback candidates if model list endpoint fails
    if not active_models:
        active_models = [
            "qwen/qwen2.5-coder-32b-instruct",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
            "mistralai/mistral-large-2-instruct",
        ]

    for model_name in active_models[:5]:  # Try top 5 available models
        try:
            print(f"  🟢 Calling NVIDIA AI ({model_name})...")
            resp = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 4096,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return strip_markdown_fences(content)
            else:
                print(f"  ⚠️ NVIDIA model {model_name} returned {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ NVIDIA model {model_name} error: {e}")
    raise RuntimeError("All NVIDIA AI models failed.")


def generate_solution(problem: dict, lang_slug: str, error_feedback: str = "") -> str:
    """Generates solution using Gemini (primary) with automatic NVIDIA AI fallback."""
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

    # Option 1: Try Gemini if key is provided
    if GEMINI_API_KEY:
        MODEL = "gemini-3.8-flash"
        MAX_MODEL_RETRIES = 3
        for attempt_n in range(1, MAX_MODEL_RETRIES + 1):
            try:
                print(f"  🤖 Calling Gemini ({MODEL}) (attempt {attempt_n}/{MAX_MODEL_RETRIES})...")
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                )
                return strip_markdown_fences(response.text)
            except Exception as e:
                err_str = str(e)
                print(f"  ⚠️ Gemini failed: {e}")
                if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt_n < MAX_MODEL_RETRIES:
                    wait = 10 * attempt_n
                    print(f"  ⏳ Waiting {wait}s for Gemini...")
                    time.sleep(wait)
                elif NVIDIA_API_KEY:
                    print("  🔄 Switching over to NVIDIA AI...")
                    break

    # Option 2: NVIDIA NIM API fallback
    if NVIDIA_API_KEY:
        return call_nvidia_ai(prompt)

    raise RuntimeError("No AI provider succeeded. Check your GEMINI_API_KEY or NVIDIA_API_KEY.")


# ──────────────────────────────────────────────
# LeetCode submit + poll with Cloudflare Resiliency
# ──────────────────────────────────────────────
def submit_with_playwright(slug: str, question_id: str, lang_slug: str, code: str) -> dict:
    """Uses a headless Chromium instance via Playwright to bypass Cloudflare Turnstile/JS challenge."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright is not installed in the current environment.")

    print("  🛡️ Launching Playwright Chromium to bypass Cloudflare challenge...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        context.add_cookies([
            {"name": "LEETCODE_SESSION", "value": LEETCODE_SESSION or "", "domain": ".leetcode.com", "path": "/"},
            {"name": "csrftoken", "value": CSRF_TOKEN or "", "domain": ".leetcode.com", "path": "/"},
        ])
        page = context.new_page()
        page_url = f"https://leetcode.com/problems/{slug}/"
        print(f"  Navigating to {page_url}...")
        page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)

        # Retrieve any refreshed csrftoken from context cookies
        cookies = context.cookies()
        csrf_val = next((c["value"] for c in cookies if c["name"] == "csrftoken"), CSRF_TOKEN or "")

        print("  Executing submission fetch inside browser session...")
        js_submit = """
        async ({ slug, csrf, lang, question_id, code }) => {
            const res = await fetch(`https://leetcode.com/problems/${slug}/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': 'https://leetcode.com',
                    'Referer': `https://leetcode.com/problems/${slug}/`,
                    'x-csrftoken': csrf
                },
                body: JSON.stringify({
                    lang: lang,
                    question_id: String(question_id),
                    typed_code: code
                })
            });
            const text = await res.text();
            try {
                return { status: res.status, json: JSON.parse(text) };
            } catch(e) {
                return { status: res.status, text: text };
            }
        }
        """
        eval_res = page.evaluate(js_submit, {
            "slug": slug,
            "csrf": csrf_val,
            "lang": lang_slug,
            "question_id": str(question_id),
            "code": code,
        })
        browser.close()

        status = eval_res.get("status")
        if status == 200 and "json" in eval_res and "submission_id" in eval_res["json"]:
            return eval_res["json"]
        raise RuntimeError(f"Playwright submission returned HTTP {status}: {eval_res.get('text', eval_res.get('json'))}")


def submit_and_poll(session, title_slug: str, question_id: str, lang_slug: str, code: str) -> dict:
    """Submits code to LeetCode and polls until the judge finishes grading.
    Handles Cloudflare challenges via browser profile rotation, warm-ups, and Playwright fallback."""
    submit_url = f"https://leetcode.com/problems/{title_slug}/submit/"

    payload = {
        "lang": lang_slug,
        "question_id": str(question_id),
        "typed_code": code,
    }

    submission_id = None
    last_error = ""

    # Tier 1: Try curl_cffi with rotating browser profiles
    for attempt_idx, profile in enumerate(BROWSER_PROFILES, 1):
        try:
            print(f"  📤 Submitting code (profile: {profile}, attempt {attempt_idx}/{len(BROWSER_PROFILES)})...")
            curr_session = session if attempt_idx == 1 else get_session(impersonate_target=profile)
            warm_up_problem_page(curr_session, title_slug)
            csrf = sync_csrf(curr_session)

            submit_headers = {
                "Content-Type": "application/json",
                "Origin": "https://leetcode.com",
                "Referer": f"https://leetcode.com/problems/{title_slug}/",
                "Accept": "*/*",
                "x-csrftoken": csrf,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": None,
                "Sec-Fetch-User": None,
            }

            resp = curr_session.post(submit_url, json=payload, headers=submit_headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if "submission_id" in data:
                    submission_id = data["submission_id"]
                    session = curr_session
                    break
                else:
                    last_error = f"200 OK without submission_id: {resp.text[:200]}"
            elif resp.status_code == 403:
                last_error = "403 Forbidden (Cloudflare WAF / Auth challenge)"
                print(f"  ⚠️ Profile {profile} hit Cloudflare 403. Retrying with next profile in 4s...")
                time.sleep(4)
            elif resp.status_code == 429:
                last_error = "429 Rate limited"
                print("  ⚠️ Rate limited. Waiting 12s...")
                time.sleep(12)
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(3)
        except Exception as e:
            last_error = str(e)
            print(f"  ⚠️ Error submitting with {profile}: {e}")
            time.sleep(3)

    # Tier 2: If curl_cffi was blocked by Cloudflare (403), fallback to Playwright headless browser
    if not submission_id:
        print("  ⚠️ curl_cffi was blocked by Cloudflare across all profiles. Attempting Playwright fallback...")
        try:
            pw_data = submit_with_playwright(title_slug, question_id, lang_slug, code)
            submission_id = pw_data.get("submission_id")
        except Exception as pw_err:
            print(f"  ❌ Playwright fallback error: {pw_err}")
            raise RuntimeError(f"Submission rejected ({last_error} | Playwright: {pw_err})")

    if not submission_id:
        raise RuntimeError(f"Submission rejected: {last_error}")

    print(f"  Submitted! Polling Submission ID: {submission_id}...")

    # Poll /submissions/detail/<id>/check/ every 3 seconds
    check_url = f"https://leetcode.com/submissions/detail/{submission_id}/check/"
    sync_csrf(session)
    for _ in range(25):
        time.sleep(3)
        try:
            check_resp = session.get(check_url, timeout=15).json()
            if check_resp.get("state") == "SUCCESS":
                return check_resp
        except Exception as e:
            print(f"  ⚠️ Polling transient error: {e}")

    return {"status_msg": "Polling Timeout"}


def save_solution(slug: str, title: str, difficulty: str, lang: str, code: str, runtime: str = "N/A", percentile: float = 0.0):
    """Saves the solved problem and code locally for GitHub commit."""
    folder = os.path.join("solutions", slug)
    os.makedirs(folder, exist_ok=True)
    ext_map = {"cpp": "cpp", "java": "java", "python3": "py"}
    ext = ext_map.get(lang, lang)

    code_path = os.path.join(folder, f"solution.{ext}")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    readme_path = os.path.join(folder, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# {title} ({difficulty})\n\n")
        f.write(f"- **Problem URL:** https://leetcode.com/problems/{slug}/\n")
        f.write(f"- **Language:** {lang.upper()}\n")
        f.write(f"- **Runtime:** {runtime} (Beats {percentile}%)\n")
        f.write(f"- **Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"```{lang}\n{code}\n```\n")
    print(f"  💾 Solution saved to {code_path}")


# ──────────────────────────────────────────────
# Fallback — Two Sum (guaranteed AC to save streak)
# ──────────────────────────────────────────────
def submit_fallback_two_sum(session):
    """Guaranteed fallback if the AI fails all attempts on the daily problem."""
    print("🚑 Attempting Two Sum fallback to protect streak...")
    cpp_code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for (int i = 0; i < nums.size(); i++) {
            if (mp.count(target - nums[i])) return {mp[target - nums[i]], i};
            mp[nums[i]] = i;
        }
        return {};
    }
};"""
    try:
        result = submit_and_poll(session, "two-sum", "1", "cpp", cpp_code)
        save_solution("two-sum", "Two Sum", "Easy", "cpp", cpp_code, result.get("status_runtime", "N/A"), round(result.get("runtime_percentile", 0), 1))
        return result
    except Exception as e:
        print(f"  ❌ Two Sum fallback failed: {e}")
        return {"status_msg": f"Fallback Failed: {e}"}


# ──────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────
def notify(msg: str):
    """Prints to stdout (visible in Actions logs) and optionally pings Discord."""
    print(msg)
    if DISCORD_WEBHOOK:
        try:
            requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=10)
        except Exception as e:
            print(f"⚠️ Discord notification error: {e}")


# ──────────────────────────────────────────────
# Main entry-point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Validate required secrets are present
    missing = [v for v in ["LEETCODE_SESSION", "CSRF_TOKEN"] if not os.getenv(v)]
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("NVIDIA_API_KEY")):
        missing.append("GEMINI_API_KEY or NVIDIA_API_KEY")
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("   Set them as GitHub Actions secrets (Settings → Secrets → Actions).")
        sys.exit(1)

    client = get_session()

    # Verify session authentication upfront
    print("🔐 Checking LeetCode authentication...")
    is_signed_in, current_user = check_auth(client)
    if not is_signed_in:
        print("⚠️ WARNING: Your LEETCODE_SESSION is invalid or has expired!")
        print("   LeetCode returns isSignedIn=False. Submissions will likely be rejected with 403.")
        print("   👉 To fix: Log into leetcode.com, copy fresh 'LEETCODE_SESSION' and 'csrftoken' cookies,")
        print("      and update them in your GitHub repo: Settings → Secrets and variables → Actions.")
        notify(
            "⚠️ **LeetCode Session Alert**\n"
            "Your `LEETCODE_SESSION` cookie appears to be expired or invalid (not signed in).\n"
            "Please copy fresh cookies from your browser and update GitHub Secrets."
        )
    else:
        print(f"   👤 Logged in as: {current_user}")

    print("🔍 Fetching today's Daily Challenge...")
    daily = get_daily_slug(client)
    print(f"   Date: {daily.get('date')} | Status: {daily.get('userStatus')}")

    # userStatus == "Finish" means today's daily coin is already earned
    if daily.get("userStatus") == "Finish":
        print("✅ Today's Daily Challenge is already completed!")
        sys.exit(0)

    slug = daily["question"]["titleSlug"]
    problem = get_problem_details(client, slug)
    print(f"🎯 Solving Daily: {problem['title']} ({problem['difficulty']}) in {TARGET_LANG}...")

    feedback = ""
    solved = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- Attempt {attempt}/{MAX_ATTEMPTS} ---")
        try:
            code = generate_solution(problem, TARGET_LANG, feedback)
        except Exception as e:
            print(f"  ❌ AI generation failed: {e}")
            break

        try:
            result = submit_and_poll(client, slug, problem["questionId"], TARGET_LANG, code)
        except Exception as e:
            print(f"  ❌ Attempt {attempt} submission failed: {e}")
            feedback = f"Submission error: {e}"
            if attempt < MAX_ATTEMPTS:
                print("  ⏳ Waiting 15s before next attempt...")
                time.sleep(15)
            continue

        status = result.get("status_msg", "Unknown Error")

        if status == "Accepted":
            runtime = result.get("status_runtime", "N/A")
            percentile = round(result.get("runtime_percentile", 0), 1)
            save_solution(slug, problem['title'], problem['difficulty'], TARGET_LANG, code, runtime, percentile)
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
        try:
            submit_fallback_two_sum(client)
        except Exception as e:
            print(f"❌ Fallback Two Sum also failed: {e}")
            notify(f"❌ Fallback Two Sum also failed: {e}")

