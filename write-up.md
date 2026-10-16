# Findings report

**Name / team:** Madushan/VisionX
**Date:** 16 October 2026
**Target:** Jack Ripsley — lab environment only

---

## Summary

I found four flags by inspecting a draft HTML file, using exposed personal information to complete account recovery, changing a file identifier in a URL, and examining a personal archive. The findings indicate exposed sensitive information, weak account recovery, and missing file-access authorization; the archive finding also raises concerns about sensitive-data protection, although the notes do not establish the cryptographic method used. Two findings were rated High and two Medium, with the draft-file rating dependent on its accessibility and the sensitivity of the exposed information.

---

## Finding 1

| | |
|---|---|
| **Flag** | `UOM{n0th1ng_1s_3v3r_r34lly_pr1v4t3}` |
| **Where** | `/jack-the-ripper/site/drafts/index.html` |
| **Severity** | High — provisional; depends on accessibility and sensitivity |

**How I got there**

1. Opened the cloned `jack-the-ripper` project directory.
2. Navigated to `site/drafts/index.html`.
3. Inspected the HTML file and found the flag.

**What was actually wrong**

Sensitive information was included in a client-side HTML file. Any user who can obtain that file can read its contents, so placing information in a draft directory does not provide access control. The notes confirm local access through the clone; they do not establish whether the file was publicly served.

**Why that severity**

The original finding was rated High because an exposed secret could allow unauthorized access to sensitive resources without authentication. That impact depends on the information being a real secret and the file being accessible to an unauthorized user; the flag alone does not demonstrate that level of harm.

**How I would fix it**

Remove secrets from client-side files, store them securely on the server, enforce authentication and authorization, and rotate any exposed credentials.

---

## Finding 2

| | |
|---|---|
| **Flag** | `UOM{s3cur1ty_qu3st10ns_4r3_n0t_s3cur1ty}` |
| **Where** | Stashbox dashboard for `jripsley92` |
| **Severity** | High |

**How I got there**

1. Visited DevForum and identified the username `jripsley92`.
2. Examined the photos folder for information that answered the account's security questions.
3. Used those answers in the password-reset process.
4. Signed in to Stashbox using the recorded lab credentials: username `jripsley92`, password `Jack123`.
5. Found the flag on the dashboard.

**What was actually wrong**

The recovery process treated knowledge of personal facts as proof of account ownership. Those facts could be discovered from exposed information, allowing someone other than the account owner to complete recovery.

**Why that severity**

An attacker could take over the account, access private information, and potentially change account settings. This directly compromises the account owner's privacy and control of the account.

**How I would fix it**

Replace security questions with verified, time-limited, single-use recovery tokens, add multi-factor authentication, and rate-limit recovery attempts.

---

## Finding 3

| | |
|---|---|
| **Flag** | `UOM{1_ch4ng3d_0n3_numb3r_4nd_1t_w0rk3d}` |
| **Where** | Website files section; accessed by changing a numeric identifier in the URL (exact URL and identifier were not recorded) |
| **Severity** | Medium |

**How I got there**

1. Navigated to the website's files section and opened a file.
2. Changed a numeric value in the URL to request a different file.
3. Accessed the different file and found the flag.

**What was actually wrong**

The application appeared to trust a user-controlled file identifier without checking whether the current user was authorized to access the requested file. This is an Insecure Direct Object Reference (IDOR), a form of broken access control.

**Why that severity**

Someone able to access the file endpoint could potentially retrieve other users' files or sensitive documents by changing identifiers. Medium reflects the demonstrated file disclosure; the notes do not establish the full range of accessible files or any ability to modify them.

**How I would fix it**

Enforce server-side authorization for every file request, checking the current user's permission for the requested resource and denying access by default.

---

## Finding 4

| | |
|---|---|
| **Flag** | `UOM{y0ur_0wn_crypt0_1s_n0t_crypt0}` |
| **Where** | `notes.txt` inside `jack-the-ripper/stashbox/files/personal-archive.zip` |
| **Severity** | Medium |

**How I got there**

1. Located `personal-archive.zip` in the Stashbox files directory.
2. Opened the archive and examined `notes.txt`.
3. Found the flag in the notes.

**What was actually wrong**

Sensitive information was readable within the accessible archive. The original finding described insecure storage or weak cryptography, but the recorded steps do not identify an encryption algorithm or demonstrate how encryption was bypassed. The evidence supports concern about archive confidentiality; a specific cryptographic flaw remains unverified.

**Why that severity**

An unauthorized person who obtained an inadequately protected archive could read confidential material. Medium reflects this potential disclosure; the notes do not establish broader access or account compromise from the archive contents.

**How I would fix it**

Restrict archive access and, where encryption is required, use a vetted library with authenticated encryption such as AES-GCM and securely managed keys.

---

## Anything else you noticed

The notes recorded a simple password, `Jack123`, for the Stashbox login, but did not establish whether it was the original password or one set during recovery. Password-policy enforcement therefore remains unverified. No other uninvestigated findings were documented.
