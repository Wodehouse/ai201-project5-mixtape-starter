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

For Bug #2: Identified the root cause myself by reading `get_friends_listening_now()`
in the feed service. The bug was hard to reproduce via API calls alone since
the seed data events all fell within today's window regardless of the cutoff
logic — so I wrote a dedicated unit test that places a listen event one second
before midnight to distinguish the rolling 24h window from the intended
"since midnight" behaviour. Used AI to help draft the RCA entry after the fix
was confirmed by the test suite.

---

## Codebase Map

`app.py` is the Flask application factory. It initialises the database,
registers the four blueprints (songs, playlists, users, feed), and exposes
`create_app()` for both the server and the test suite.

`models.py` defines the five SQLAlchemy models — `User`, `Song`, `Playlist`,
`ListeningEvent`, and `Notification` — plus three association tables:
`song_tags`, `playlist_entries` (which stores an explicit `position` column
for ordered songs), and `friendships` (a bidirectional self-referential
many-to-many on `User`).

`routes/` contains four blueprint files — `songs.py`, `playlists.py`,
`users.py`, and `feed.py`. Each route does input parsing and response
formatting only; all business logic is immediately delegated to a
corresponding service function.

`services/` is where all the logic lives. Each service file maps to a
feature domain: `feed_service.py` handles the listening-now feed,
`streak_service.py` handles listening streaks, `playlist_service.py`
handles playlist queries, `search_service.py` handles song search, and
`notification_service.py` handles notification creation.

Data flow — user listens to a song:
A `POST /songs/<id>/listen` request hits `routes/songs.py`, which calls
`streak_service.record_listening_event()`. That function creates a
`ListeningEvent` row, then calls `streak_service.update_listening_streak()`
to update the user's streak. All database writes happen inside the service
layer; the route only formats and returns the JSON response.

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
with no index error.

---

### Bug #2 — Friends Listening Now shows people from yesterday

**How I reproduced it:**
The bug was difficult to reproduce via API calls alone because the seed
data events all fall within today's window regardless of which cutoff
logic is used. Instead I wrote a unit test in `tests/test_feed.py` that
places a friend's listen event one second before midnight
(`start_of_today - timedelta(seconds=1)`). This timestamp sits inside
the old rolling 24-hour window but before today's midnight boundary —
the exact condition that exposes the difference between the buggy and
fixed behaviour. The test `test_excludes_events_from_yesterday` failed
before the fix and passed after.

**How I found the root cause:**
Read `get_friends_listening_now()` in `services/feed_service.py`. The
cutoff was computed as:
```python
cutoff = datetime.now(timezone.utc) - RECENT_THRESHOLD
```
where `RECENT_THRESHOLD = timedelta(hours=24)`. This creates a rolling
24-hour window rather than a same-calendar-day window, which is what the
feature description requires.

**Root cause:**
`RECENT_THRESHOLD` was set to `timedelta(hours=24)`, making the cutoff
a point 24 hours in the past rather than the start of the current
calendar day. A friend who listened at 11pm last night would still
appear at 9am the next morning because 10 hours is within the 24-hour
window — but they are clearly not listening "now" or even "today".

**Fix and side-effect check:**
Replaced the rolling threshold cutoff with a midnight-of-today cutoff:
```python
cutoff = datetime.combine(datetime.now(timezone.utc), time.min)
```
This anchors the window to the start of the current UTC day rather than
a rolling 24-hour period. The deduplication logic (`seen_friends` set)
and ordering (`desc(listened_at)`) are untouched. All five tests in
`tests/test_feed.py` pass after the fix, including the regression test
that specifically targets the yesterday-boundary case.

---

## Git Log Screenshot

<!-- Paste screenshot of `git log --oneline` on bugfix/mixtape branch -->