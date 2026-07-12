01 · DATA & DURABILITY
Databases & data
Your database is the one thing you can't rebuild from a prompt. Everything here is about making sure that when something goes wrong, and it will, you don't lose data, you can find out who changed what, and the app stays fast as it grows.

01
Maintain separate databases for development and production.
The agent will reuse one database for everything unless you stop it, and the first time you tell it to "clear the test data" you'll wipe real customers. Spin up a separate dev database on day one, and never let your local environment point at production.

02
Soft deletes only. Never hard-delete user-facing records.
Add a deleted_at timestamp instead of running DELETE. A soft-deleted row can be brought back when a user emails "I didn't mean to remove that"; a hard-deleted one is gone forever. It also saves you the day the agent writes a delete query that's missing its WHERE clause.

03
Automated daily backups, stored somewhere outside your hosting provider.
Replit, Supabase, Railway, Neon: they all have great days and bad days. If your only backup lives on the same platform as your database, one outage or billing mishap takes both at once. Push a daily dump to S3, Google Drive, or Backblaze so your data survives your host.

04
Test restoring a backup at least once before you need to.
A backup you've never restored is a wish, not a backup. Once, right now, download yesterday's dump and rebuild a throwaway database from it. The day you discover the backups were empty, corrupt, or in the wrong format should not be the day production is down.

05
Add created_at, updated_at, created_by, updated_by to every table from day one.
These four columns cost nothing today and are nearly impossible to backfill later. They answer "when did this happen?" and "who did this?", which are questions you'll ask during every bug report, dispute, and security review. Tell the agent to add them to every table by default.

06
Use UUIDs instead of sequential IDs for anything user-facing.
If your order URLs look like /orders/1041, anyone can change the number and probe for other people's orders, and a competitor can read your growth off the ID. Use UUIDs (or another non-guessable ID) for anything that shows up in a URL, an email, or an API response. Keep sequential IDs internal if you like, just don't expose them.

07
Add indexes for the columns you filter, sort, and join on.
A query that's instant on the hundred rows in testing can crawl on the hundred thousand rows you'll have in six months, and the agent rarely adds indexes on its own. Any column you regularly search by, sort by, or join on wants an index. If a page gets slow, this is the first thing to check.

08
Change the schema with migration files, not by hand-editing the database.
Every change to your tables should be a migration file that's committed to git and run the same way in dev, staging, and production. Hand-editing the production database is how staging and prod quietly drift apart until a deploy breaks. Ask the agent to use your framework's migration tool, and run new migrations on a copy first.

02 · SECRETS & KEYS
Secrets & access
Every API key, password, and database URL is a loaded gun. The fastest way to leak one is to hand it to the agent in chat or commit it to git, both of which happen constantly. Treat secrets like cash: kept in one place, never in transit when you can avoid it, and re-issued the moment they might have been seen.

09
Never paste API keys, passwords, or DB URLs into the agent chat.
Anything you type into the chat may be logged, stored, or shown in a transcript later. Put secrets in environment variables, Replit Secrets, or your host's secret manager, and let the code read them from there. If you've already pasted one, treat it as leaked and rotate it.

10
Rotate any credential the agent has ever seen, before going live.
Keys that passed through chat logs, screenshots, or a public repo aren't yours alone anymore. Before launch, regenerate every API key, database password, and token the agent touched, and update only the secret store. It's ten minutes now versus a drained account later.

11
Separate API keys for dev and prod, so a leaked dev key can't touch real users.
Use a sandbox or test key while building, and a separate live key in production. A dev key that leaks then can't charge real cards, send real emails, or read real data. Stripe, OpenAI, Twilio, SendGrid and most others hand you both, so use them.

12
Keep .env in .gitignore, and check the repo to confirm nothing sensitive ever got committed.
The agent commits fast and doesn't always respect .gitignore. Make sure .env and any credentials file are ignored, then actually search your git history (git log -p) for keys and passwords. If you find one, rotate it: deleting the file from the latest commit doesn't remove it from history.

03 · AUTH
Authentication & authorization
Authentication is "are you logged in?" Authorization is "are you allowed to see this particular thing?" Agents are decent at the first and routinely skip the second, which is how user A ends up reading user B's invoices. Don't build your own login system, and test the access checks yourself.

13
Don't roll your own auth. Use Auth0, Clerk, Supabase Auth, Firebase Auth, or similar.
Password hashing, sessions, email verification, password resets, rate limiting, breach detection: a managed auth provider does all of it correctly, and free at your scale. Hand-rolled auth is where the worst bugs live. Pick a provider and move on.

14
Test the "logged in as A, hit B's URL" attack on every page that shows user data.
Log in as one user, grab a URL or API call that loads their data, then change the ID in it to someone else's while still logged in as the first user. If you see the second user's data, every record in your app is effectively public. Run this check on every screen that shows anything user-specific.

15
Make session cookies Secure, HttpOnly, and SameSite.
Secure stops the cookie from traveling over plain HTTP, HttpOnly stops JavaScript (and therefore most XSS) from stealing it, and SameSite blocks a lot of cross-site request forgery. Good auth providers set these for you, but if any session or "remember me" cookie is hand-rolled, check the flags. It's a one-line fix that closes a whole class of attack.

16
Force re-authentication for destructive actions (delete account, change email, export data).
Deleting an account, changing the login email, exporting all data, transferring ownership: make the user re-enter their password or re-confirm right before it happens. It blocks an attacker who walks up to an unlocked laptop, and it makes "I didn't do that" far less likely. The agent won't add this unless you ask.

04 · ADMIN
Admin panel & internal tools
You will need to look something up, fix a bad record, refund someone, or flip a flag, at 11pm, from your phone, without the agent. That's what an admin panel is for. Build one early, gate it properly, and log everything that happens inside it, because admin access is the most dangerous access in the system.

17
Build a real admin panel for menus, users, and master data, and put DB backup downloads in it (SQL and Excel).
Not raw SQL access: a screen where you (or a non-technical teammate) can manage menus and master data, look up and edit users, and see core records. Add one-click export of the whole database in SQL and in Excel, so you can pull a backup or hand finance a spreadsheet without touching the agent. This is the difference between a five-minute fix and a one-hour incident.

18
Put the admin panel behind its own login and a non-obvious path, ideally with a second factor.
Don't mount it at /admin with the same login as everyone else. Give it its own route that isn't guessable, re-check on every admin page that the user is actually an admin (not just hiding the menu link), and turn on two-factor for admin accounts. The admin panel can change anything, so it should be the hardest thing in your app to get into.

19
Admin role should be a database flag, not a hardcoded email or "if user.id == 1".
When admin is is_admin = true in the database, you can grant and revoke it instantly and you always have a list of who has it. When it's an email address buried in the code, adding a second admin means a code change and a deploy, and you'll forget who's privileged. Make it data, not code.

20
Log every admin action: who deleted what, who changed which price.
Admin users can change anything, so "who did this, and when?" has to be answerable for every admin action: edits, deletions, refunds, role grants, price changes. Write it to an append-only audit log the moment it happens. The day a price is wrong or a record vanishes, that log is the only thing standing between you and a guess.

21
Use a separate staging admin account. Never test destructive features as the founder account.
Your personal account is the one that owns the company, so don't use it to try out "delete all", "bulk refund", or a half-built admin button. Keep a throwaway admin account in staging for that. The whole point of testing is to break things, so make sure the thing that breaks isn't you.

05 · INPUT
User input & validation
Anything that comes from a browser, including form fields, uploaded files, URL parameters, and API calls, is written by someone you don't control, and sometimes by someone trying to hurt you. The agent validates in the browser because that's where the form is. You need it validated on the server, where it actually counts.

22
Validate everything on the server, not just in the browser. The browser is the user's territory.
Browser-side checks are a convenience for honest users; they vanish the moment someone opens dev tools or hits your API directly. Every rule, including required fields, max lengths, allowed values, and numbers that must be positive, has to be enforced again on the server. If the agent only added the front-end check, the validation isn't real.

23
Cap file upload size and restrict file types. Agents almost always forget this.
Without a limit, one user can upload a 4 GB file and fill your disk or your bill; without a type check, they can upload something executable. Set a hard max size and an allowlist of extensions and content types on the server, and reject everything else. This is the single most consistently missing piece in agent-built upload features.

24
Rate-limit your own endpoints, especially login, signup, password reset, and anything that emails or texts.
Unlimited login attempts means password guessing; an unlimited "send reset email" button means someone uses you to spam (and bill) their way through a mailing list. Put a per-IP and per-account rate limit on the sensitive endpoints. Most frameworks have a one-line middleware for this, so ask for it explicitly.

25
Sanitize anything one user can show another (comments, profiles, messages). XSS is still everywhere.
If user A can put a <script> tag in a comment and user B's browser runs it, you have stored XSS, and now A can act as B. Escape or sanitize user content everywhere it's shown to someone else. Modern frameworks handle a lot of this by default, but the moment the agent renders raw HTML "so the formatting works", the hole is back.

06 · COST CONTROL
Costs & limits
Pay-as-you-go pricing plus an agent that writes loops is a combination that bills in your sleep. None of these services stop charging you on their own, so the limits have to come from you, before launch, not after the invoice.

26
Set hard spending limits on every paid service (AWS, OpenAI, Twilio, SendGrid) before launch.
AWS, Google Cloud, OpenAI, Anthropic, Twilio, SendGrid: each has a budget cap or hard-limit setting. Set them now, set them low, and raise them deliberately. A cap that emails you at 80% and stops at 100% is the difference between "huh, busy day" and a four-figure surprise.

27
Cap LLM token usage per user per day if your app calls an AI API.
If your app calls a model, one user (or one bot) can run up a bill that has nothing to do with revenue. Track tokens per user per day and cut them off, or queue them, past a sane limit. Decide what a normal user costs you, and don't let anyone cost a hundred times that.

28
Watch for agent-written loops that hit paid APIs. One infinite loop overnight is a $4k bill.
The classic: a retry loop with no backoff, or a "process all items" job that re-queues itself. It runs fine in testing with three rows, then runs forever in production. Read any code that calls a paid API inside a loop and make sure there's a ceiling on iterations and a real stop condition.

29
Use a separate billing-alert email that actually pings your phone.
Budget alerts sent to an inbox you check on Tuesdays are useless during a Saturday incident. Route billing and usage alerts to an address (or a number) that pushes a notification to your phone immediately. The entire value of an alert is that you see it in minutes, not days.


Want this explained out loud?
I'm Praneeth. I break down AI concepts, papers, and projects into short reels in Telugu, with working demos so the ideas stick.

Follow on Instagram
The playlists →
07 · ENVIRONMENTS
Deployment & environments
There's the version on your laptop, the version real users touch, and, ideally, a copy in between where you can break things safely. Most agent-built projects have only the first two, wired together loosely, with production still in debug mode. Tightening this up is mostly flipping settings.

30
Three environments minimum: local dev, staging, production. Test in staging with prod-like data first.
Local is where you and the agent work; production is sacred; staging is a near-identical copy of production where you try the scary change with prod-like data before customers see it. If "deploy" currently means "push straight to the thing customers use", add a staging step. It's the cheapest insurance you'll buy.

31
Disable debug mode, stack traces, and verbose errors in production. They leak code structure to attackers.
A stack trace on an error page hands an attacker your framework, your file paths, your database structure, sometimes your secrets. Set the environment to production, turn off debug, and show users a plain "something went wrong" while the details go to your logs. Frameworks ship with this; agents leave it on.

32
Set CORS to your actual domain, not "*".
Access-Control-Allow-Origin: * means any website on the internet can call your API from a logged-in user's browser. Lock it to your own domain or domains. The agent uses * because it makes the error go away during development, so change it before launch.

33
Use HTTPS everywhere. No exceptions, even for "internal" tools.
Plain HTTP means passwords, session cookies, and data travel in the clear over every coffee-shop network in between. HTTPS is free (Let's Encrypt, or automatic on Vercel, Netlify, Cloudflare) and non-negotiable, including for admin panels and "just for the team" tools, which handle the most sensitive stuff you have.

34
Health-check endpoint plus uptime monitoring (UptimeRobot, BetterStack: free tiers exist).
Add a tiny /health endpoint that returns OK, and point a free monitor at it. Now you find out the site is down from a text message instead of from an angry customer. Two minutes to set up, and it tells you about the outage you'd otherwise sleep through.

35
If your app sends email, set up SPF, DKIM, and DMARC for your domain, or it lands in spam.
Password resets, receipts, notifications: if the receiving mail servers can't verify the mail really came from you, a lot of it goes to spam or gets dropped, and you won't know. Your email provider (Postmark, Resend, SendGrid, SES) has a guide for adding those three DNS records. Set them up before launch, then send yourself a test and confirm it landed in the inbox.

08 · LOGGING
Logging & observability
When a user says "it broke" and you can't see what happened, you're debugging blind, and re-asking them to reproduce a bug they've already moved on from. A little logging turns "no idea" into "here's the exact error." Just be careful what you write down.

36
Log errors to a service (Sentry, LogRocket, or even a file you can grep). You can't fix what you can't see.
Send exceptions and errors somewhere durable, with a stack trace and enough context to reproduce them. Sentry's free tier is plenty to start. The alternative is hearing about bugs only from the users annoyed enough to email you, which is a small fraction of the ones actually hitting them.

37
Don't log passwords, full credit cards, or PII even by accident. Mask sensitive fields in logs.
Logs get shared, exported, and shipped to third-party services, so they aren't a safe place for secrets. Mask or omit passwords, full card numbers, tokens, and personal data before anything is written. "We leaked it through our logs" is a real and embarrassing way to have a breach.

38
Keep at least 30 days of logs. Bugs report themselves weeks later.
A user hits something on the 3rd and emails you on the 20th. If your logs only go back a week, that report is unactionable. Thirty days, or more if you can afford it, covers the lag between "thing happened" and "someone finally told you."

09 · CODE & GIT
Code & version control
Git is your undo button, and the agent's diff is the only window you have into what it actually did. Used well, you can roll back any bad change in seconds. Used carelessly, with no commits and blind "accept all", you're trusting a machine with no memory not to quietly break something that worked.

39
Commit to git before every major agent change. The undo button is your best friend.
Before you let the agent do anything significant, commit. If the change goes sideways, and "add this feature" sometimes rewrites three others, you're one command from the last known-good state. Frequent commits are free; reconstructing a working app from memory is not.

40
Read the diff before accepting it. If you don't understand a chunk, ask the agent to explain it line by line.
Skim every change the agent proposes; if a chunk doesn't make sense, have it walk you through that chunk before you accept. "Accept all" without looking is how a fix to the login page also loosens a permission check three files over. You don't have to write the code, but you do have to know what changed.

41
Keep a plain-English doc of what your app does and why. You write this, not the agent.
One document: what the app does, who uses it, and the rules that must always hold ("users can only see their own orders", "refunds over $100 need approval"). When the agent rewrites a feature and "forgets" a rule, this doc is how you catch it. It's your source of truth; the code is just the current attempt at implementing it.

42
For anything touching payments, auth, or sensitive data: pay a human dev for a one-hour review before launch.
An hour of a real engineer's time, looking specifically at how you handle money, logins, and personal data, is the best money you'll spend on this project. They'll spot the missing authorization check or the unsafe query that you and the agent both walked past. Cheap insurance against the failures that actually make the news.

10 · LEGAL
Legal & compliance
The moment you collect an email address, you've taken on obligations, and the agent will never bring them up. None of this requires a lawyer to get started, but skipping it entirely is the kind of mistake that's cheap to fix now and expensive to fix after a complaint.

43
Privacy policy and terms of service before you collect a single user email.
You need to tell people what you collect, why, and what they can do about it, and you need terms that set the rules for using your service. Generators and templates get you a reasonable first version in an hour. Launching without them isn't "moving fast", it's just exposure.

44
Know which laws apply to you: GDPR (EU), DPDP (India), CCPA (California), HIPAA (health data).
Where your users live decides what you must do: GDPR for the EU, DPDP for India, CCPA and CPRA for California, HIPAA for US health data, and more. They have real teeth and the agent won't warn you. Spend an afternoon finding out which ones apply, before you're big enough to be worth a complaint.

45
A "delete my account" feature that actually deletes (or fully anonymizes). Required in most jurisdictions.
Most privacy laws give users a right to be erased, and a button that just sets active = false doesn't count. Build a real path that deletes or irreversibly anonymizes their data, and make sure your backups and logs eventually age it out too. Far easier to design in now than to retrofit under a deadline.

46
Cookie-consent banner if you have EU users.
If you use analytics, ads, or other non-essential cookies and you have EU visitors, you need real consent before those cookies load, not a banner that's purely decorative. A consent-management tool handles this in an afternoon. Annoying, yes; optional, no.

11 · OPS
Operational hygiene
Everything above keeps the app correct. This keeps you sane when it isn't. The common thread: write the plan down while it's calm, make sure the system can tell you something's wrong before a customer does, and make sure the project doesn't live or die with you alone.

47
Document the recovery steps for your top 3 disasters: DB corrupted, hosting down, key leaked.
For each one, write the exact steps now: where the backups are and how to restore them, who to call and what to flip if the host is down, how to rotate every credential fast. Mid-incident at 2am is the worst possible time to figure this out. A page of notes you wrote calmly is worth more than any tool.

48
Have a way to put the site in maintenance mode without redeploying.
Sometimes the right move is to take the site down on purpose, for a bad migration or a security scramble, and you don't want that to depend on a working deploy pipeline. A single flag (an env var, a row in a table) that flips the app to a "back soon" page gives you a clean pause button. Build it before you need it.

49
Email/SMS alerts for: failed payments, signup spikes, error-rate spikes, server down.
Define what "something's wrong" looks like, including payments failing, a weird flood of signups, errors climbing, and the server unreachable, and wire each one to an alert that reaches your phone. The goal is to hear it from your monitoring, not from Twitter. Start with a handful; just make sure they actually fire.

50
Make sure someone other than you can get into hosting, the database, the domain, and email, and that renewals won't lapse.
If you're unreachable for a week, can a co-founder or a trusted person log into your host, your database, your domain registrar, and the email account that controls password resets for all of them? Keep those credentials somewhere shared and safe (a password manager), and put calendar reminders on the domain and SSL certificate renewals. Plenty of apps have died because a domain quietly expired or the only person with access went dark.

