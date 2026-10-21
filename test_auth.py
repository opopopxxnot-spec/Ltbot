"""
Local diagnostic script to verify your LeetCode session and cookies.
Run this anytime locally to check if your LEETCODE_SESSION is valid.

Usage:
    python test_auth.py
"""

import os
import sys
from curl_cffi import requests

GRAPHQL_URL = "https://leetcode.com/graphql"

def main():
    print("=" * 55)
    print(" 🔍 LeetCode Session & Cookie Diagnostic Tool")
    print("=" * 55)

    session_cookie = os.getenv("LEETCODE_SESSION")
    csrf_cookie = os.getenv("CSRF_TOKEN")

    if not session_cookie:
        session_cookie = input("\n👉 Paste your LEETCODE_SESSION cookie: ").strip()
    if not csrf_cookie:
        csrf_cookie = input("👉 Paste your csrftoken cookie: ").strip()

    if not session_cookie or not csrf_cookie:
        print("❌ Both LEETCODE_SESSION and csrftoken are required.")
        sys.exit(1)

    print("\n⏳ Testing connection and authentication with LeetCode...")

    s = requests.Session(impersonate="chrome124")
    s.headers.update({
        "Content-Type": "application/json",
        "Origin": "https://leetcode.com",
        "Referer": "https://leetcode.com/",
        "Accept": "*/*",
        "x-csrftoken": csrf_cookie,
    })
    s.cookies.set("LEETCODE_SESSION", session_cookie, domain=".leetcode.com")
    s.cookies.set("csrftoken", csrf_cookie, domain=".leetcode.com")

    # 1. Check Auth Status
    auth_query = """
    query globalData {
      userStatus {
        isSignedIn
        username
        realName
        userSlug
      }
    }
    """
    try:
        resp = s.post(GRAPHQL_URL, json={"query": auth_query}, timeout=15)
        data = resp.json().get("data", {}).get("userStatus", {})
        is_signed_in = data.get("isSignedIn", False)
        username = data.get("username", "")
    except Exception as e:
        print(f"❌ Failed to reach LeetCode API: {e}")
        sys.exit(1)

    if not is_signed_in:
        print("\n❌ SESSION INVALID OR EXPIRED!")
        print("   LeetCode rejected this session (isSignedIn = False).")
        print("   👉 Fix: Log into leetcode.com in your browser, copy fresh cookies,")
        print("      and paste them here / update your GitHub Secrets.")
        sys.exit(1)

    print(f"\n✅ AUTHENTICATION SUCCESSFUL!")
    print(f"   👤 Username: {username}")

    # 2. Check Today's Challenge & Status
    daily_query = """
    query questionOfToday {
      activeDailyCodingChallengeQuestion {
        date
        userStatus
        question {
          title
          difficulty
        }
      }
    }
    """
    try:
        daily_resp = s.post(GRAPHQL_URL, json={"query": daily_query}, timeout=15)
        daily_data = daily_resp.json().get("data", {}).get("activeDailyCodingChallengeQuestion", {})
        date = daily_data.get("date", "N/A")
        status = daily_data.get("userStatus", "N/A")
        q_title = daily_data.get("question", {}).get("title", "N/A")
        q_diff = daily_data.get("question", {}).get("difficulty", "N/A")

        print(f"\n📅 Today's Challenge ({date}):")
        print(f"   Problem: {q_title} ({q_diff})")
        print(f"   Status for {username}: {status} {'(Completed ✅)' if status == 'Finish' else '(Not Solved Yet ⏳)'}")
    except Exception as e:
        print(f"⚠️ Could not fetch daily challenge status: {e}")

    print("\n" + "=" * 55)
    print("🎉 Your cookies are 100% VALID and ready to use in GitHub Secrets!")
    print("=" * 55)

if __name__ == "__main__":
    main()
