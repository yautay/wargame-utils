"""Who speaks with authority in a game's forums.

XML API2 does not link credited persons to BGG accounts, so the owner lists them in wgu.yaml (`bgg.authorities`).
A cached user whose first and last name equal a credited designer/developer gets a provisional role with
a question mark (`designer?`); `suggest()` turns such matches into YAML entries for the owner to approve.
"""
from __future__ import annotations

from .xmlapi import normalize_name

ROLES = ("designer", "developer", "publisher", "player", "other")
BOOST = {"designer": 1.0, "developer": 0.8, "publisher": 0.6}


def configured(authorities: list[dict] | None) -> dict[str, dict]:
    out = {}
    for a in authorities or []:
        if isinstance(a, dict) and a.get("user") and a.get("role") in ROLES:
            out[str(a["user"]).casefold()] = a
    return out


def credited_names(game: dict | None) -> dict[str, tuple[str, dict]]:
    """normalized person name → (role, person) for designers and developers of the game."""
    out: dict[str, tuple[str, dict]] = {}
    for role, key in (("developer", "developers"), ("designer", "designers")):  # designer wins on a tie
        for p in (game or {}).get(key, []):
            out[normalize_name(p["name"])] = (role, p)
    return out


def full_name(user: dict | None) -> str:
    if not user:
        return ""
    return normalize_name(f"{user.get('firstname', '')} {user.get('lastname', '')}")


class Roles:
    """Resolve the role of a post author: configured → name match (with '?') → player."""

    def __init__(self, authorities: list[dict] | None, game: dict | None, users: list[dict]):
        self.conf = configured(authorities)
        names = credited_names(game)
        self.matched: dict[str, str] = {}
        for u in users:
            role = names.get(full_name(u))
            if role and u.get("username"):
                self.matched[u["username"].casefold()] = role[0] + "?"

    def role(self, username: str) -> str:
        key = (username or "").casefold()
        if key in self.conf:
            return self.conf[key]["role"]
        return self.matched.get(key, "player")

    def users_with_role(self, role: str) -> list[str]:
        """Usernames for a role filter; `designer` includes provisional `designer?` matches."""
        base = role.rstrip("?")
        out = [a["user"] for a in self.conf.values() if a["role"] == base]
        out += [u for u, r in self.matched.items() if r == base + "?" and u not in self.conf]
        return out

    def authorities(self) -> list[str]:
        return [a["user"] for a in self.conf.values() if a["role"] not in ("player", "other")] + \
            [u for u in self.matched if u not in self.conf]


def boost(role: str) -> float:
    base = role.rstrip("?")
    return BOOST.get(base, 0.0) * (0.5 if role.endswith("?") else 1.0)


def suggest(game: dict | None, posters: list[tuple[str, int]], users: dict[str, dict | None],
            authorities: list[dict] | None, min_posts: int = 3) -> list[dict]:
    """Entries for wgu.yaml `bgg.authorities` from name matches (owner approves them)."""
    conf = configured(authorities)
    names = credited_names(game)
    out = []
    for username, n in posters:
        if n < min_posts or username.casefold() in conf:
            continue
        hit = names.get(full_name(users.get(username)))
        if hit:
            role, person = hit
            out.append({"user": username, "role": role, "person": person["id"],
                        "note": f"dopasowanie nazwiska: {person['name']}; postów: {n}; do potwierdzenia"})
    return out
