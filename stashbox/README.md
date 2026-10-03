# Stashbox — the target app

A deliberately vulnerable personal-file-storage app. **Standard library only** — there is
nothing to `pip install`, which is deliberate: installs are what kill workshops.

```bash
cd stashbox
python3 app.py            # http://localhost:8080
PORT=9000 python3 app.py  # if 8080 is taken
```

Serves on `0.0.0.0`, so participants on the same network can reach it at
`http://<your-ip>:8080`. State lives in memory — **restart the process to reset**.

## What's wrong with it (on purpose)

1. **Password recovery via a security question** whose answer is discoverable OSINT.
   This is the intended Stage 2 path.
2. **Username enumeration** — `/forgot` tells you whether an account exists. Real flaw,
   and here it helps participants confirm they have the right username.
3. **`/download?id=N` performs no ownership check.** The hole for Stage 3 is already
   open; there is simply no other user's file to find yet. Adding one turns Stage 3 on.

## Concurrency note

`passwords` is a **set**, and a reset *adds* to it rather than replacing. So thirty
students resetting Jack's password against one instance never lock each other out —
every password anyone sets keeps working. Without this the room races and half of them
get locked out on the same screen.
