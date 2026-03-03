# TaskFlow Pro — Product Documentation

## 1. Getting Started

### 1.1 Creating an Account
1. Visit taskflowpro.com/signup
2. Enter your email and create a password
3. Verify your email address
4. Choose your plan (Free, Starter, Professional, Enterprise)
5. Set up your first workspace

### 1.2 Creating a Workspace
A workspace is your team's home in TaskFlow Pro. Each workspace can contain multiple projects.
- Click "New Workspace" from the dashboard
- Name your workspace and invite team members via email
- Assign roles: Owner, Admin, Member, Guest

### 1.3 User Roles & Permissions
| Role   | Create Projects | Manage Members | Billing | Delete Workspace |
|--------|----------------|----------------|---------|------------------|
| Owner  | Yes            | Yes            | Yes     | Yes              |
| Admin  | Yes            | Yes            | No      | No               |
| Member | Yes            | No             | No      | No               |
| Guest  | No             | No             | No      | No               |

## 2. Core Features

### 2.1 Boards
- **Kanban Boards:** Drag-and-drop columns (To Do, In Progress, Done, or custom)
- **List View:** Traditional list with sorting and filtering
- **Calendar View:** See tasks by due date (Professional+)
- **Gantt View:** Timeline visualization (Professional+)

### 2.2 Tasks
- **Create a task:** Click "+" in any column or use keyboard shortcut `Ctrl+N`
- **Task fields:** Title, description, assignee, due date, priority (Low/Medium/High/Urgent), labels, attachments
- **Subtasks:** Break tasks into smaller items; parent task shows progress %
- **Comments:** @mention teammates, attach files, use markdown
- **Activity log:** Every change is tracked with timestamps

### 2.3 Team Collaboration
- **@mentions:** Tag teammates in comments or task descriptions
- **Real-time updates:** Changes sync instantly across all devices
- **Notifications:** Email, in-app, and mobile push notifications
- **File sharing:** Drag-and-drop files into tasks (storage limits per plan)

### 2.4 Time Tracking (Professional+)
- Start/stop timer on any task
- Manual time entry
- Weekly time reports per team member
- Export timesheets to CSV

### 2.5 Automations (Professional+)
- **Rule-based:** "When task moves to Done, notify channel"
- **Scheduled:** "Every Monday, create standup task"
- **Templates:** Pre-built automation recipes
- Limit: 50 automations on Professional, unlimited on Enterprise

### 2.6 Integrations
| Integration | Tiers          | Description                        |
|-------------|----------------|------------------------------------|
| Slack       | Starter+       | Notifications, create tasks from Slack |
| GitHub      | Professional+  | Link PRs to tasks, auto-update status  |
| Google Drive| Starter+       | Attach Drive files to tasks            |
| Jira        | Enterprise     | Two-way sync with Jira projects        |
| Zapier      | Professional+  | Connect to 5000+ apps                  |
| API Access  | Professional+  | REST API with OAuth2 authentication    |

## 3. API Basics (Professional+)

### 3.1 Authentication
```
POST https://api.taskflowpro.com/oauth/token
Content-Type: application/json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "grant_type": "client_credentials"
}
```

### 3.2 Key Endpoints
- `GET /api/v1/projects` — List all projects
- `POST /api/v1/tasks` — Create a task
- `GET /api/v1/tasks/{id}` — Get task details
- `PUT /api/v1/tasks/{id}` — Update a task
- `GET /api/v1/users` — List workspace members

### 3.3 Rate Limits
- Professional: 100 requests/minute
- Enterprise: 500 requests/minute

## 4. Common How-Tos

### How to move a task between boards
1. Open the task
2. Click the "Board" dropdown
3. Select the destination board and column

### How to set up recurring tasks
1. Open the task
2. Click "Repeat" icon
3. Choose frequency (daily, weekly, monthly, custom)
4. A new task is auto-created when the current one is completed

### How to export project data
1. Go to Project Settings → Export
2. Choose format: CSV, JSON, or PDF
3. Select date range and fields
4. Click "Export" — file downloads or is emailed for large exports

### How to enable two-factor authentication (2FA)
1. Go to Account Settings → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code to confirm

### How to archive a project
1. Go to Project Settings → General
2. Click "Archive Project"
3. Archived projects are read-only but searchable
4. Unarchive anytime from the Archived Projects section

## 5. Frequently Asked Questions

**Q: Can I switch plans at any time?**
A: Yes, upgrades take effect immediately. Downgrades take effect at the end of the billing cycle. No penalties for switching.

**Q: Is there a mobile app?**
A: Yes, TaskFlow Pro is available on iOS and Android. All features except Gantt view are available on mobile.

**Q: How do I cancel my subscription?**
A: Go to Billing Settings → click "Cancel Subscription." Your data is retained for 30 days after cancellation.

**Q: What happens to my data if I downgrade?**
A: Features beyond your new plan are disabled, but no data is deleted. If you exceed storage limits, you won't be able to upload new files until you free space or upgrade.

**Q: Do you offer refunds?**
A: We offer a 14-day money-back guarantee for first-time subscribers. After that, refunds are handled case-by-case by our billing team.

**Q: Can I import from other tools?**
A: Yes, we support direct import from Trello, Asana, Monday.com, and Jira. Go to Workspace Settings → Import.

**Q: Is my data encrypted?**
A: Yes, all data is encrypted in transit (TLS 1.3) and at rest (AES-256). Enterprise plans include additional compliance certifications (SOC 2, GDPR).

**Q: What is the uptime guarantee?**
A: Enterprise plans include a 99.5% uptime SLA. All plans benefit from our redundant infrastructure with 99.9% historical uptime.

## 6. Known Issues & Workarounds
- **Gantt view slow with 500+ tasks:** Workaround — use filters to limit visible tasks.
- **Slack notifications delayed occasionally:** Check Slack webhook status in Integration settings.
- **CSV export missing custom fields:** Fix planned for v3.2. Workaround — use JSON export.

## 7. Contact Support
- **Email:** support@taskflowpro.com
- **Live Chat:** Available on taskflowpro.com (business hours, 9am–6pm PT)
- **WhatsApp:** +1-555-TASKFLOW (Starter+ plans)
- **Help Center:** help.taskflowpro.com
