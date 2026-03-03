# TaskFlow Pro — Knowledge Base (Searchable)

## TOPIC: Account & Workspace Setup
- Create account at taskflowpro.com/signup → verify email → choose plan → create workspace
- Workspace = team home, contains multiple projects
- Invite members via email from workspace settings
- Roles: Owner (full control), Admin (manage members/projects), Member (create tasks/projects), Guest (view only)
- Transfer workspace ownership: Settings → General → Transfer Ownership → enter new owner email
- Delete workspace: Only Owner can delete. Settings → Danger Zone → Delete Workspace (irreversible after 30 days)

## TOPIC: Boards & Views
- Board types: Kanban (drag-drop columns), List View, Calendar View (Professional+), Gantt View (Professional+)
- Default columns: To Do, In Progress, Done — customizable
- Create board: "+" button on sidebar or Ctrl+B
- Archive board: Board Settings → Archive (read-only, searchable, reversible)
- Duplicate board: Board menu → Duplicate (copies all tasks, assignees, labels)
- Known issue: Gantt view slow with 500+ tasks — use filters to limit visible tasks

## TOPIC: Tasks
- Create task: "+" in column or Ctrl+N
- Task fields: title, description (markdown), assignee, due date, priority (Low/Medium/High/Urgent), labels, attachments
- Set due date: Open task → click calendar icon next to "Due Date" → pick date
- Subtasks: Open task → "Add Subtask" button below description. Parent shows % completion
- Recurring tasks: Open task → Repeat icon → choose frequency. New task created when current completed
- Move task between boards: Open task → Board dropdown → select destination
- Bulk task creation: Not available via UI. Use API (POST /api/v1/tasks) or CSV import via Workspace Settings → Import
- Comments: @mention teammates, markdown supported, file attachments
- Activity log: Every change tracked with timestamps, visible in task sidebar

## TOPIC: Collaboration
- @mentions: Type @ in comments or descriptions to tag teammates
- Real-time sync across all devices
- Notifications: email, in-app, mobile push — customize at Settings → Notifications
- Notification settings: Choose per-event (mentions, due dates, assignments, comments) — toggle email/push/in-app independently
- File sharing: drag-drop into tasks, storage limits per plan

## TOPIC: Time Tracking (Professional+ only)
- Enable: Project Settings → Features → Toggle "Time Tracking"
- Start timer: Open any task → click play button
- Manual entry: Open task → Time Tracking section → "Add Entry"
- Reports: Project menu → Time Reports → filter by member/date
- Export: Time Reports → Export CSV

## TOPIC: Automations (Professional+ only)
- Access: Project Settings → Automations
- Rule-based: trigger → condition → action (e.g., "When status changes to Done → notify #channel")
- Scheduled: time-based triggers ("Every Monday at 9am → create standup task")
- Limit: 50 automations on Professional, unlimited on Enterprise
- Known issue: Some automations may not trigger if task is updated via API — check automation logs

## TOPIC: Integrations
- Slack (Starter+): Workspace Settings → Integrations → Slack → Connect. Sends notifications, create tasks from Slack with /taskflow command
- GitHub (Professional+): Project Settings → Integrations → GitHub → Authorize. Links PRs to tasks. Auto-status update requires webhook configuration in GitHub repo settings
- Google Drive (Starter+): Workspace Settings → Integrations → Google Drive → Connect. Attach Drive files to tasks
- Jira (Enterprise): Two-way sync. Contact support for setup assistance
- Zapier (Professional+): Search "TaskFlow Pro" in Zapier app directory. If not found, use the direct link from Integrations page
- API (Professional+): REST API with OAuth2. Docs at api.taskflowpro.com/docs

## TOPIC: API
- Authentication: OAuth2 client credentials flow
- Token endpoint: POST https://api.taskflowpro.com/oauth/token
- Token lifetime: 1 hour (use refresh token for long-lived access)
- Rate limits: Professional 100 req/min, Enterprise 500 req/min
- Key endpoints: GET /projects, POST /tasks, GET /tasks/{id}, PUT /tasks/{id}, GET /users
- Webhooks: Available on Professional+. Configure at Project Settings → Webhooks → Add Endpoint

## TOPIC: Plans & Pricing
- Free: $0/mo, 5 users, basic boards, 3 boards max, 1 GB storage
- Starter: $9/user/mo, 25 users, unlimited boards, file attachments, 10 GB storage
- Professional: $19/user/mo, unlimited users, custom workflows, time tracking, Gantt/Calendar views, API access, 100 GB storage
- Enterprise: Custom pricing, SSO, audit logs, dedicated support, unlimited storage, 99.5% SLA
- Upgrades: immediate effect. Downgrades: end of billing cycle
- Annual billing: ~20% discount (contact sales for exact pricing)
- No penalties for switching plans
- 14-day money-back guarantee for first-time subscribers

## TOPIC: Security & Privacy
- Encryption: TLS 1.3 in transit, AES-256 at rest
- 2FA: Settings → Security → Enable 2FA → scan QR with authenticator app
- 2FA recovery: If phone lost and no backup codes, contact support with account verification for reset
- SSO: Enterprise only (SAML 2.0). Configured by workspace admin
- Audit logs: Enterprise only. Track all user actions
- Data residency: US data centers (EU data residency available for Enterprise)
- Compliance: SOC 2 Type II, GDPR compliant. HIPAA — contact sales for BAA

## TOPIC: Import & Export
- Import from: Trello, Asana, Monday.com, Jira — Workspace Settings → Import
- Export: Project Settings → Export → choose CSV, JSON, or PDF
- CSV export known issue: custom fields not included (fix in v3.2). Workaround: use JSON export
- Data retained 30 days after account cancellation

## TOPIC: Mobile App
- Available on iOS and Android
- All features except Gantt view available on mobile
- Known issue: Android app may crash when opening tasks with many attachments — fix in next update
- Offline mode: Not currently available (on roadmap)

## TOPIC: Guest Users
- Guests can: view tasks, view boards, view files
- Guests cannot: create tasks, edit tasks, leave comments, manage members
- To allow external collaboration: upgrade guests to Member role or use Starter+ plan
- Guest limit: Unlimited guests on all plans
