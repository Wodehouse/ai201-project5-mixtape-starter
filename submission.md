# Mixtape Bug Hunt — submission.md

---

## AI Usage

For Bug #1: After tracing the code myself and identifying the root cause,
I used AI to help draft the root cause analysis entry based on my findings.
I provided the code and my diagnosis; the AI helped structure and articulate
the written response. All code reading, tracing, and the fix itself were done
independently.

<!-- Add entries for subsequent bugs here as you fix them -->

---

## Codebase Map

<!-- Write this before starting any bug work — Milestone 1 -->
<!-- Cover: main files and their roles, data flow for at least one feature -->

---

## Root Cause Analysis

---

### Bug #1 — My listening streak keeps resetting

**How I reproduced it:**
Listened on a Saturday, then listened again on Sunday. Called
`GET /users/<id>/streak` and saw the streak show 1 instead of
incrementing from the previous day's count. Confirmed the Sunday
streak test was previously failing and passed after the fix.

**How I found the root cause:**
Started from `app.py` to understand the app entry point, then navigated
to the `services/` folder and found the function responsible for streak
updates: `update_listening_streak()`. Read through the conditional logic
and the extra weekday guard in the `elif` branch immediately stood out
as suspicious.

**Root cause:**
`today.weekday()` returns 6 for Sunday. The `elif` condition was:
```python
elif days_since_last == 1 and today.weekday() != 6:
```
On any Sunday, `today.weekday() != 6` evaluates to `False`, causing a
valid consecutive-day listen to fall through to the `else` branch, which
resets the streak to 1. Every Sunday listen was treated as a missed day
regardless of whether the user had listened on Saturday.

**Fix and side-effect check:**
Removed `and today.weekday() != 6` from the `elif` condition:
```python
elif days_since_last == 1:
    user.listening_streak += 1
```
The `days_since_last == 1` check already correctly identifies a
consecutive-day listen — the weekday guard was both unnecessary and
wrong. The `days_since_last == 0` (already listened today) and `else`
(missed a day) branches are untouched and unaffected. Ran tests and
confirmed the previously failing Sunday streak test now passes.

---

### Bug #2 — Friends Listening Now shows people from yesterday

**How I reproduced it:**
<!-- Fill in after Milestone 2 -->

**How I found the root cause:**
<!-- Fill in after investigation -->

**Root cause:**
<!-- Fill in -->

**Fix and side-effect check:**
<!-- Fill in -->

---

### Bug #3 — The same song keeps showing up twice in search

**How I reproduced it:**
<!-- Fill in after Milestone 2 -->

**How I found the root cause:**
<!-- Fill in after investigation -->

**Root cause:**
<!-- Fill in -->

**Fix and side-effect check:**
<!-- Fill in -->

---

### Bug #4 — No notification when a song is rated

**How I reproduced it:**
<!-- Fill in after Milestone 2 -->

**How I found the root cause:**
<!-- Fill in after investigation -->

**Root cause:**
<!-- Fill in -->

**Fix and side-effect check:**
<!-- Fill in -->

---

### Bug #5 — Last song in a playlist never shows up

**How I reproduced it:**
<!-- Fill in after Milestone 2 -->

**How I found the root cause:**
<!-- Fill in after investigation -->

**Root cause:**
<!-- Fill in -->

**Fix and side-effect check:**
<!-- Fill in -->

---

## Git Log Screenshot

<!-- Paste screenshot of `git log --oneline` on bugfix/mixtape branch -->
<!-- Should show one commit per bug fix with fix: prefix -->