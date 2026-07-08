"""
tests/test_feed.py — Mixtape

Tests for the "Friends Listening Now" feed logic.

Regression focus: get_friends_listening_now must only surface friends who
listened *today*, not anyone in a trailing 24-hour window. An event from
exactly 24h ago always falls before the start of today (unless it is exactly
midnight), so it is the precise case that distinguishes the intended
"since midnight" behaviour from the old rolling-24h-window bug — which is why
it is hard to reproduce by hand.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app import create_app, db
from models import User, Song, ListeningEvent
from services.feed_service import get_friends_listening_now


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def _make_user(username):
    u = User(username=username, email=f"{username}@example.com")
    db.session.add(u)
    db.session.flush()
    return u


def _make_song(sharer, title="Midnight Drive"):
    s = Song(title=title, artist="The Wanderers", shared_by=sharer.id)
    db.session.add(s)
    db.session.flush()
    return s


def _listen(user, song, listened_at):
    e = ListeningEvent(user_id=user.id, song_id=song.id, listened_at=listened_at)
    db.session.add(e)
    db.session.flush()
    return e


def test_excludes_events_from_yesterday(app):
    """A friend whose only listen was late yesterday must NOT appear.

    The event sits one second before the start of today: still inside a
    trailing-24h window (so the old cutoff `now - 24h` would surface it) but
    on the wrong calendar day (so the "since midnight" cutoff excludes it).
    This is the exact gap that distinguishes the fix from the bug.
    """
    with app.app_context():
        me = _make_user("me")
        friend = _make_user("darius")
        me.friends.append(friend)
        song = _make_song(me)

        start_of_today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        _listen(friend, song, start_of_today - timedelta(seconds=1))
        db.session.commit()

        feed = get_friends_listening_now(me.id)
        assert feed == []


def test_includes_events_from_today(app):
    """A friend who listened moments ago appears in the feed."""
    with app.app_context():
        me = _make_user("me")
        friend = _make_user("darius")
        me.friends.append(friend)
        song = _make_song(me)

        now = datetime.now(timezone.utc)
        _listen(friend, song, now - timedelta(minutes=1))
        db.session.commit()

        feed = get_friends_listening_now(me.id)
        assert len(feed) == 1
        assert feed[0]["friend"]["username"] == "darius"
        assert feed[0]["song"]["title"] == "Midnight Drive"


def test_shows_only_most_recent_song_per_friend(app):
    """When a friend has several listens today, only their latest song shows."""
    with app.app_context():
        me = _make_user("me")
        friend = _make_user("darius")
        me.friends.append(friend)
        older = _make_song(me, title="Old Track")
        newer = _make_song(me, title="New Track")

        now = datetime.now(timezone.utc)
        _listen(friend, older, now - timedelta(hours=2))
        _listen(friend, newer, now - timedelta(minutes=5))
        db.session.commit()

        feed = get_friends_listening_now(me.id)
        assert len(feed) == 1
        assert feed[0]["song"]["title"] == "New Track"


def test_returns_empty_when_no_friends(app):
    """A user with no friends gets an empty feed."""
    with app.app_context():
        me = _make_user("me")
        db.session.commit()

        assert get_friends_listening_now(me.id) == []


def test_unknown_user_raises_value_error(app):
    """Looking up a non-existent user raises ValueError (routed to a 404)."""
    with app.app_context():
        with pytest.raises(ValueError):
            get_friends_listening_now("does-not-exist")
