#!/usr/bin/env python3
"""
Stashbox — Stage 2 target for the jack-the-ripper lab.

DELIBERATELY VULNERABLE. Run only on a machine you own, for teaching.
Standard library only — nothing to pip install.

    python3 app.py                # http://localhost:8080
    PORT=9000 python3 app.py

State is in memory: restart the process to reset all passwords.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse, html, uuid, os, sys, hashlib, base64

PORT = int(os.environ.get("PORT", "8080"))
HERE = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(HERE, "files")

def _f(b):
    """Flags are stored encoded so that a casual `grep -r UOM{` through the source
    does not hand the whole exercise over. This is not security - it is etiquette
    enforcement. Read the source properly and you will of course find them."""
    return base64.b64decode(b).decode()


FLAG_STAGE2 = _f("VU9Ne3MzY3VyMXR5X3F1M3N0MTBuc180cjNfbjB0X3MzY3VyMXR5fQ==")
FLAG_STAGE3 = _f("VU9NezFfY2g0bmczZF8wbjNfbnVtYjNyXzRuZF8xdF93MHJrM2R9")

# ── data ───────────────────────────────────────────────────────────────────────
USERS = {
    "jripsley92": {
        "name": "Jack Ripsley",
        "email": "jack.ripsley92@mailbox.invalid",
        # Long and random: NOT guessable. The only way in is the reset flow.
        # A set, not a string, so simultaneous resets by different students
        # never lock each other out.
        "passwords": {"Xq7vR2mLp94fZt"},
        "question": "What was the name of your first pet?",
        # sha-256 of the answer, lowercased and stripped - not the answer itself
        "answer_sha256": "914ccee57b252e420137fa3f665c67482e5d9a95bb860ce17bcc78e1a06ac653",
        "flag": FLAG_STAGE2,
    },
    "a_perera": {
        "name": "Anushka Perera",
        "email": "a.perera@mailbox.invalid",
        "passwords": {"Kd8sQ1zWp07nYb"},
        "question": "What street did you grow up on?",
        "answer_sha256": "d3b9bd0b2e1f0ba0b0f0a1a4d1b7f7a9f0ee2f8a3c4d5e6f708192a3b4c5d6e7",
        "flag": None,
    },
    "m_fernando": {
        "name": "Marlon Fernando",
        "email": "m.fernando@mailbox.invalid",
        "passwords": {"Rw4tHn6vLx23Qm"},
        "question": "What was your first car?",
        "answer_sha256": "a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00",
        "flag": None,
    },
}

# Numeric ids on purpose — this is the hook Stage 3 (IDOR) hangs off.
FILES = {
    2: {"owner": "a_perera",   "name": "holiday-plan.txt"},
    3: {"owner": "m_fernando", "name": "appraisal-notes.txt", "inject": True},
    5: {"owner": "jripsley92", "name": "cv-2023.txt"},
    6: {"owner": "jripsley92", "name": "synth-patches.txt"},
    7: {"owner": "jripsley92", "name": "personal-archive.zip"},
}

SESSIONS = {}  # sid -> username


# ── helpers ────────────────────────────────────────────────────────────────────
def page(title, body, shell=False):
    wrap = ('<div class="shell">' + body + "</div>") if shell else \
           ('<div class="center"><div class="card">' + body + "</div></div>")
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{html.escape(title)} · Stashbox</title>"
        "<link rel=\"stylesheet\" href=\"/static/app.css\"></head><body>"
        + wrap + "</body></html>"
    ).encode()


BRAND = '<div class="brand">stash<span>box</span></div>'


def human_size(path):
    try:
        n = os.path.getsize(path)
    except OSError:
        return "—"
    return f"{n} B" if n < 1024 else f"{n/1024:.1f} KB"


class Handler(BaseHTTPRequestHandler):
    server_version = "Stashbox/1.4"

    def log_message(self, fmt, *a):
        sys.stderr.write("  %s - %s\n" % (self.address_string(), fmt % a))

    # ---- plumbing ----
    def _send(self, code, body=b"", ctype="text/html; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _redirect(self, to, cookie=None):
        extra = [("Location", to)]
        if cookie:
            extra.append(("Set-Cookie", cookie))
        self._send(303, b"", extra=extra)

    def _form(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8", "replace")
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}

    def _user(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                if k == "sb_session":
                    return SESSIONS.get(v)
        return None

    # ---- routes ----
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        path = u.path

        if path == "/":
            return self._redirect("/login")

        if path == "/static/app.css":
            try:
                with open(os.path.join(HERE, "static", "app.css"), "rb") as f:
                    return self._send(200, f.read(), "text/css; charset=utf-8")
            except OSError:
                return self._send(404, b"not found", "text/plain")

        if path == "/login":
            note = ""
            if q.get("reset"):
                note = '<div class="ok">Password updated. Sign in with your new password.</div>'
            if q.get("e"):
                note = '<div class="err">That username and password did not match.</div>'
            return self._send(200, page("Sign in", BRAND + f"""
<h1>Sign in to Stashbox</h1>
<p class="sub">Your files, wherever you are.</p>
<form method="post" action="/login">
<label for="username">Username</label>
<input id="username" name="username" type="text" autocomplete="off" autofocus>
<label for="password">Password</label>
<input id="password" name="password" type="password" autocomplete="off">
<button type="submit">Sign in</button>
</form>{note}
<p class="alt"><a href="/forgot">Forgotten your password?</a></p>"""))

        if path == "/forgot":
            who = (q.get("u") or [""])[0].strip().lower()
            if not who:
                note = '<div class="err">We have no account with that username.</div>' if q.get("e") else ""
                return self._send(200, page("Reset", BRAND + f"""
<h1>Reset your password</h1>
<p class="sub">Tell us who you are and we will ask your security question.</p>
<form method="post" action="/forgot">
<label for="username">Username</label>
<input id="username" name="username" type="text" autocomplete="off" autofocus>
<button type="submit">Continue</button>
</form>{note}
<p class="alt"><a href="/login">Back to sign in</a></p>"""))
            rec = USERS.get(who)
            if not rec:
                return self._redirect("/forgot?e=1")
            note = '<div class="err">That is not the answer we have on file.</div>' if q.get("e") else ""
            return self._send(200, page("Security question", BRAND + f"""
<h1>Hello, {html.escape(rec['name'].split()[0])}</h1>
<p class="sub">Answer your security question to choose a new password.</p>
<div class="q"><p class="lbl">Security question</p><p>{html.escape(rec['question'])}</p></div>
<form method="post" action="/reset">
<input type="hidden" name="username" value="{html.escape(who)}">
<label for="answer">Your answer</label>
<input id="answer" name="answer" type="text" autocomplete="off" autofocus>
<label for="newpass">New password</label>
<input id="newpass" name="newpass" type="password" autocomplete="off">
<button type="submit">Set new password</button>
</form>{note}
<p class="alt"><a href="/login">Back to sign in</a></p>"""))

        if path == "/dashboard":
            who = self._user()
            if not who:
                return self._redirect("/login")
            rec = USERS[who]
            rows = ""
            for fid, f in sorted(FILES.items()):
                if f["owner"] != who:
                    continue
                size = human_size(os.path.join(FILES_DIR, f["name"]))
                rows += (f'<tr><td><a href="/download?id={fid}">{html.escape(f["name"])}</a></td>'
                         f'<td class="sz">{size}</td></tr>')
            return self._send(200, page("Your files", f"""
<div class="top">{BRAND}<div class="who">{html.escape(rec['name'])} &middot;
<a href="/help">help</a> &middot; <a href="/logout">sign out</a></div></div>
<div class="flag"><p class="lbl">Stage 2 complete</p><code>{html.escape(rec['flag'])}</code></div>
<h2 style="font-size:16px;margin:0 0 12px">Your files</h2>
<table><tr><th>Name</th><th>Size</th></tr>{rows}</table>""", shell=True))

        if path == "/help":
            return self._send(200, page("Help", f"""
<div class="top">{BRAND}<div class="who"><a href="/dashboard">back to your files</a></div></div>
<h2 style="font-size:17px;margin:0 0 4px">Help &amp; FAQ</h2>
<p class="sub">Short answers to the things people ask us most.</p>

<div class="faq"><h3>Sharing a file with someone</h3>
<p>Every file you upload gets a permanent link of its own. Open the file and copy the
address straight out of your browser &mdash; it will look something like
<code>/download?id=42</code>. Send that to whoever needs it and they can download it
directly, no fuss.</p>
<p>Links never expire and never change, so you can paste one into a document once and
forget about it.</p></div>

<div class="faq"><h3>Is my data private?</h3>
<p>Absolutely. Your files are visible only to you. Nobody else using Stashbox can see
what is in your account, and we never look.</p></div>

<div class="faq"><h3>I have forgotten my password</h3>
<p>No problem &mdash; use the <a href="/forgot">reset link</a> on the sign-in page and
answer your security question. Choose a question only you could possibly answer.</p></div>

<div class="faq"><h3>How much can I store?</h3>
<p>5&nbsp;GB on the free plan. Upgrade any time from your account settings.</p></div>""",
                                        shell=True))

        if path == "/download":
            who = self._user()
            if not who:
                return self._redirect("/login")
            try:
                fid = int((q.get("id") or ["0"])[0])
            except ValueError:
                return self._send(400, b"bad id", "text/plain")
            f = FILES.get(fid)
            if not f:
                return self._send(404, page("Not found", BRAND +
                                            "<h1>No such file</h1>"))
            # NOTE: there is no ownership check on this line. That is the point.
            full = os.path.join(FILES_DIR, f["name"])
            try:
                with open(full, "rb") as fh:
                    data = fh.read()
            except OSError:
                return self._send(404, b"missing on disk", "text/plain")
            if f.get("inject"):
                # kept out of the file on disk so the repo cannot simply be grepped
                data = data.replace(b"{{FLAG}}", FLAG_STAGE3.encode())
            return self._send(200, data, "application/octet-stream",
                              [("Content-Disposition",
                                f'attachment; filename="{f["name"]}"')])

        if path == "/logout":
            raw = self.headers.get("Cookie") or ""
            for part in raw.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    if k == "sb_session":
                        SESSIONS.pop(v, None)
            return self._redirect("/login", "sb_session=; Max-Age=0; Path=/")

        return self._send(404, page("Not found", BRAND + "<h1>Page not found</h1>"))

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        form = self._form()

        if path == "/login":
            who = form.get("username", "").strip().lower()
            pw = form.get("password", "")
            rec = USERS.get(who)
            if rec and pw in rec["passwords"]:
                sid = uuid.uuid4().hex
                SESSIONS[sid] = who
                return self._redirect("/dashboard",
                                      f"sb_session={sid}; Path=/; HttpOnly; SameSite=Lax")
            return self._redirect("/login?e=1")

        if path == "/forgot":
            who = form.get("username", "").strip().lower()
            if who not in USERS:
                return self._redirect("/forgot?e=1")
            return self._redirect(f"/forgot?u={urllib.parse.quote(who)}")

        if path == "/reset":
            who = form.get("username", "").strip().lower()
            ans = form.get("answer", "").strip().lower()
            new = form.get("newpass", "")
            rec = USERS.get(who)
            if not rec:
                return self._redirect("/forgot?e=1")
            ans_hash = hashlib.sha256(ans.encode()).hexdigest()
            if ans_hash != rec["answer_sha256"] or len(new) < 1:
                return self._redirect(f"/forgot?u={urllib.parse.quote(who)}&e=1")
            rec["passwords"].add(new)   # add, never replace
            return self._redirect("/login?reset=1")

        return self._send(404, b"not found", "text/plain")


if __name__ == "__main__":
    print(f"\n  Stashbox (lab target)  ->  http://localhost:{PORT}")
    print(f"  files served from       {FILES_DIR}")
    print("  deliberately vulnerable - lab use only. ctrl-c to stop.\n")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
