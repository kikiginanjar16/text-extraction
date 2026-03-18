from __future__ import annotations

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "invoice": ("invoice", "bill to", "amount due", "tax invoice", "subtotal"),
    "receipt": ("receipt", "change due", "cashier", "thank you for your purchase"),
    "contract": ("agreement", "terms and conditions", "party", "signature", "contract"),
    "proposal": ("proposal", "scope of work", "deliverables", "pricing"),
    "report": ("report", "summary", "findings", "analysis", "overview"),
    "presentation": ("agenda", "slide", "presentation", "key takeaways"),
    "resume": ("resume", "experience", "education", "skills", "curriculum vitae"),
    "memo": ("memo", "to:", "from:", "subject:"),
    "meeting_notes": ("meeting notes", "action items", "discussion", "attendees"),
    "letter": ("dear", "sincerely", "regards"),
    "form": ("form", "checkbox", "submit", "application"),
    "spreadsheet": ("sheet", "cell", "row", "column", "worksheet"),
    "manual": ("manual", "instructions", "step", "procedure"),
}

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "finance": ("budget", "forecast", "revenue", "expense", "financial", "cash flow"),
    "accounting": (
        "general ledger",
        "journal entry",
        "accounts payable",
        "accounts receivable",
        "reconciliation",
    ),
    "it": ("system", "infrastructure", "server", "deployment", "incident", "application", "security"),
    "hr": ("employee", "payroll", "recruitment", "benefits", "performance review"),
    "legal": ("clause", "compliance", "regulation", "legal", "agreement"),
    "procurement": ("vendor", "purchase order", "supplier", "tender", "procurement"),
    "operations": ("operations", "workflow", "process", "capacity", "logistics"),
    "sales": ("customer", "pipeline", "quota", "sales", "deal"),
    "marketing": ("campaign", "audience", "brand", "marketing", "lead generation"),
    "customer_support": ("ticket", "support", "customer issue", "sla", "resolution"),
    "executive": ("board", "executive", "strategy", "okr", "leadership"),
    "general": ("document", "notes", "information"),
}

TAG_HINTS: dict[str, tuple[str, ...]] = {
    "budget": ("budget", "forecast"),
    "quarterly_report": ("quarterly", "q1", "q2", "q3", "q4"),
    "security": ("security", "vulnerability", "incident"),
    "compliance": ("compliance", "regulation", "audit"),
    "roadmap": ("roadmap", "milestone"),
    "operations": ("operations", "workflow", "process"),
    "payroll": ("payroll",),
    "purchase_order": ("purchase order", "po "),
}
