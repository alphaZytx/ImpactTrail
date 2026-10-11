# S&P Global & Crisil Campus Hackathon 2026

## Submission Guidelines

## 1. How to Package & Ship Your Case Study Deliverables

We recommend keeping your entire submission self-contained inside a single **Public GitHub repository**. If you prefer cloud storage for your slides or video walkthrough, you may host them on **YouTube (unlisted)**, provided permissions are explicitly configured for public access (see Section 6).

| # | Deliverable | What to Submit | Where to Put It | Key Requirements |
|---|---|---|---|---|
| 1 | Source Code & Architecture | Working code + architecture flow/diagram | Public GitHub repo | Include dependencies and clear setup + run commands. |
| 2 | Presentation Deck | 5-7 slides (PDF or PPTX) | `/docs/presentation.pdf` in repo, link in README | Cover problem approach, system design, key results, and domain impact. |
| 3 | Demo Video Walkthrough | 10 mins screen recording | Link in README.md - YouTube (unlisted) | Quick end-to-end working demonstration of your prototype or dashboard. |
| 4 | All data to be submitted | CSV/JSON used to run your prototype | `/data` folder in repo | Submit all data and data sources used, including synthetic data. Do not use proprietary data. |

Finalists will pitch their solutions and demonstrate their innovation to the jury panel.

| # | Deliverable | What to Submit | Where to Put It | Key Requirements |
|---|---|---|---|---|
| 1 | Live Jury Pitch | Live demo + Q&A | Virtual jury panel session | Present your solution and answer technical questions. |

## 2. Content Guidance for Deck, Video & Pitch

### 2.1 Presentation Deck (5-7 slides) - suggested outline

| Slide | Topic | What to show |
|---|---|---|
| 1 | Title | Project title, candidate name, college |
| 2 | Problem & Approach | Business problem in your own words; your solution approach |
| 3 | System Design | Architecture diagram and data flow |
| 4 | Implementation Highlights | Key modules, tech choices and why |
| 5 | Key Results | Outputs, metrics, screenshots, efficiency gains vs. naive approach |
| 6 | Domain Impact | Why it matters from a use case or business standpoint |
| 7 | Limitations & Next Steps | (Optional) Assumptions, gaps, future work |

### 2.2 Demo Video (5 mins) suggested flow

- **Intro (≈30s):** Problem and what the prototype does.
- **Setup/Run (≈30s):** Show the app starting from the README commands.
- **End-to-end walkthrough (≈2-3 min):** Input data → processing → output/dashboard.
- **Results & impact (≈30-60s):** Key outputs and why they matter.

### 2.3 Live Jury Pitch (recommended: presentation + Q&A)

- For selected candidates, we will have a live jury pitch round as well.
- Expect technical questions on your design choices, code, data assumptions, and use case interpretation.
- Have the prototype running and ready to demo live.

## 3. Suggested Repository Structure

A clean, standardized folder structure helps the review team evaluate and run your code efficiently:

```text
<college>-<candidate-name>-hackathon/
|-- README.md             <-- Overview, setup steps, architecture & demo link
|-- requirements.txt      <-- Dependencies (or package.json / pom.xml)
|-- LICENSE               <-- Mandatory (MIT recommended; repo must be public)
|-- src/                  <-- Application, data pipelines, and model source code
|-- data/                 <-- Sample or synthetic dataset used for demo
`-- docs/
    |-- presentation.pdf  <-- 5-7 slide presentation deck
    `-- architecture.png  <-- High-resolution architecture diagram
```

- **Naming convention:** `<college>-<candidate-name>-hackathon` (avoid generic names like `my-hackathon-project` to prevent collisions).
- **Entry point:** Any entry point is allowed, but the exact run command must be stated in the README Quickstart.

## 4. Mandatory README.md Template

Every repository must contain a README.md at the root folder. Please use the structure below to make your submission easy to review and run.

````markdown
# [Project Title] - S&P Global & Crisil Campus Hackathon

**Candidate Name:** [Your Full Name]
**College Email ID:** [your_id@college.ac.in]
**College / Campus:** [Your College Name]
**Demo Video Link:** [YouTube / Unlisted]
**Slide Deck Link (if hosted externally):**

## 1. Project Overview / Problem Statement & Approach
A concise 2-3 paragraph summary explaining the business/technical problem you
solved and your solution approach.

## 2. Architecture & Tech Stack
- Overview of system design and data flow (embed your architecture diagram here).
- Key frameworks, databases, and AI/ML libraries used.

## 3. Dataset Used
- Source/nature of sample data (synthetic or publicly available).
- Any assumptions made about the data.

## 4. Quickstart & Installation
Runtime: [e.g., Python 3.11 / Node 20 / Java 17] on [OS tested]

Step-by-step commands to set up the environment and run your code locally:
```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt

<your run command, e.g. python main.py>
```

## 5. Key Results & Domain Impact
- What your prototype outputs/demonstrates.
- Why it matters from a use case or business standpoint.
````

## 5. Access & Permissions Checklist: before submitting your links, verify:

1. **GitHub Visibility:** Repository must be **Public**. Private repositories cannot be accessed or evaluated by the review team.
2. **Demo Video:** Must be on **YouTube as Unlisted**. Confirm it plays in an incognito/private window.
3. **Cloud Storage Access for slides (No Google Drive / OneDrive Please):**
   - Do not leave permissions as "Restricted to your university/organization domain".
   - Set link access explicitly to **"Anyone with the link can view"**.
   - Test the link in an incognito/private browser window before submitting.

## 6. AI Usage & Academic Integrity

- **AI Usage:** Use of AI assistance is generally allowed for building your solution, provided it is used with integrity and full academic/professional honesty.

## 7. Team Composition

**Team Size:** 1 (individual submissions only).

## 8. IP Ownership & Confidentiality

- This case study is a **simulated exercise** for learning and assessment purposes only.
- All work you submit (code, deck, video) is your own for portfolio/demonstration use.
- Do not source, reference, or reuse any real/confidential client data, names, or engagement details from S&P Global or Crisil. Use only synthetic or publicly available data.

## 9. Dataset Source Clarity

- No restriction on dataset source - you may use **synthetic data you generate yourself or publicly available datasets**, as long as it reasonably represents the problem you're solving.
- Clearly state the dataset source and any assumptions in the "Dataset Used" section of your README.

## 10. Disqualification Criteria

A submission will be disqualified if any of the following apply:

- Repository is **private** or inaccessible at review time.
- Demo video or slide deck links are broken, expired, or restricted (not publicly viewable).
- No live jury pitch attendance with no prior communication/valid reason.
- Evidence of plagiarism or submission of a pre-existing/copied project.
- Use of real confidential client data in violation of Section 9.

## 11. Tie-Breaker Rule

If two or more participants receive the same total score, ranking will be decided by (in order):

- Higher score in **Domain Understanding**.
- Higher score in **Presentation & Communication**.
- Earlier submission timestamp.

## 12. Live Pitch Logistics

- Live jury pitch sessions will be **pre-scheduled**; participants will be informed of their date/time slot in advance, so no separate booking is needed.

## 13. Support & Contact

- For submission issues or queries, contact: **[support-email@placeholder.com]**

## 14. Additional Guidelines

- Repository hygiene: Keep the repo free of large binary/data dumps.Commit history: Prefer incremental commits showing your build process over a single final commit.
- Final submission version: Ensure all final files and links are submitted before the deadline.
- Updates made after the deadline may not be considered.

## 15. Submission Deadline & Format

Please submit your final GitHub repository link, demo video link, and presentation deck by the communicated deadline through the official submission form. Live jury pitch slots will be shared with shortlisted participants in advance.
