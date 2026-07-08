# Mixtape Bug Hunt — submission.md

---

## AI Usage

For Bug #1: After tracing the code myself and identifying the root cause,
I used AI to help draft the root cause analysis entry based on my findings.
I provided the code and my diagnosis; the AI helped structure and articulate
the written response. All code reading, tracing, and the fix itself were done
independently.

For Bug #5: Identified the root cause myself by reading `get_playlist_songs()`
in the playlist service. Used AI to help draft the RCA entry after confirming
the fix.

---

## Codebase Map

<!-- Write this before starting any bug work — Milestone 1 -->
<!-- Cover: main files and their roles, data flow for at least one feature -->

---

## Root Cause Analysis

---

### Bug #1 — My listening streak keeps resetting

**How I reproduced it:**
Ran the existing test suite before touching any code. The Sunday streak
test was already failing — it set up a Saturday listen followed by a
Sunday listen and asserted the streak incremented, but got a reset to 1
instead. The failing test confirmed the reported behavior without needing
to trigger it manually via the API.

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

### Bug #5 — The last song in a playlist never shows up

**How I reproduced it:**
Ran `pytest tests/test_playlists.py` before touching any code. Two tests
failed: `test_playlist_returns_all_songs` (asserted 5 songs, got 4) and
`test_playlist_returns_songs_in_order` (list stopped at Track 4, missing
Track 5). No manual API calls were needed — the failing tests confirmed
the reported behavior directly.

**How I found the root cause:**
Navigated to the playlist service and read `get_playlist_songs()`. The
query itself is correct — it fetches all songs ordered by position. The
bug was on the return line at the bottom of the function.

**Root cause:**
The return statement used a Python slice that strips the last element:
```python
return [song.to_dict() for song in songs[:-1]]
```
`songs[:-1]` returns every element except the last one. Since songs are
ordered by position (ascending), the last element is always the most
recently added song — exactly matching the reported behavior where the
newest song is always the missing one, and adding another song "frees"
the previous last song while hiding the new one.

**Fix and side-effect check:**
Removed the `[:-1]` slice:
```python
return [song.to_dict() for song in songs]
```
The query ordering and all other logic is untouched. Ran
`pytest tests/test_playlists.py` and both previously failing tests now
pass. Verified that an empty playlist still returns an empty list
(no index error on an empty `songs`).

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

## Git Log Screenshot

<!-- Paste screenshot of `git log --oneline` on bugfix/mixtape branch -->
<!-- Should show one commit per bug fix with fix: prefix -->