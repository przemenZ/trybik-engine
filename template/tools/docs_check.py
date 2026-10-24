#!/usr/bin/env python3
"""Spójność dokumentacji procesu (tylko stdlib).

Źródło prawdy o statusie pracy = front-matter ticketów w docs/tickets/.
docs/BACKLOG.md jest widokiem GENEROWANYM z ticketów — nie edytuje się go ręcznie.

  python3 tools/docs_check.py          # walidacja; exit 1 przy błędach (także gdy BACKLOG.md nieaktualny)
  python3 tools/docs_check.py --write  # regeneruje docs/BACKLOG.md, potem waliduje
  python3 tools/docs_check.py --next   # wypisuje kolejny ticket; exit 1, gdy brak albo gdy błędy mogą zmienić wybór
                                       # (ready/in-progress, QUESTIONS, zależności); błędy szkiców/STATE/BACKLOG tylko sygnalizuje
  python3 tools/docs_check.py --new "Tytuł"  # nowy szkic z docs/templates/ticket.md: kolejne T-NNN, rank na końcu
                                             # kolejki, BACKLOG.md odświeżony; wypisuje ścieżkę pliku
  python3 tools/docs_check.py --check T-NNN  # sprawdza szkic tak, jakby był `ready` (pliku nie zmienia)
"""
import re
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TICKETS = DOCS / "tickets"
BACKLOG = DOCS / "BACKLOG.md"
QUESTIONS = DOCS / "QUESTIONS.md"
STATE = DOCS / "STATE.md"
TEMPLATE = DOCS / "templates" / "ticket.md"

STATUSES = ("draft", "ready", "in-progress", "done", "dropped")
KINDS = ("logic", "plain")
MAX_STATE_LINES = 40
TICKET_ID = re.compile(r"^T-\d+$")
# nagłówek pytania: `## Q-001 — Tytuł`; jako separator przyjmujemy też – - :
Q_HEADER = re.compile(r"^## (Q-\d+) *[—–:-] *(.*)$", re.M)


class Ticket:
    def __init__(self, path, fields, body):
        self.path = path
        self.fields = fields
        self.body = body
        self.id = fields.get("id", "")
        self.title = fields.get("title", "")
        self.status = fields.get("status", "")
        self.kind = fields.get("kind", "logic")
        self.depends = split_list(fields.get("depends", ""))
        try:
            self.rank = float(fields.get("rank", ""))
        except ValueError:
            self.rank = float("inf")

    def layer(self, letter):
        m = re.search(rf"^# {letter}\. [^\n]*\n(.*?)(?=^# [ABC]\. |\Z)", self.body, re.S | re.M)
        return m.group(1) if m else None

    def criteria(self):
        a = self.layer("A") or ""
        return re.findall(r"^- \[([ xX])\] (AC\d+)\b", a, re.M)

    def covered_criteria(self):
        """AC oznaczone w nawiasach ([AC1] lub [AC1, AC2]) tylko w sekcji `## Scenariusze` warstwy C; None = brak sekcji"""
        c = self.layer("C") or ""
        m = re.search(r"^## Scenariusze\b[^\n]*\n(.*?)(?=^## |\Z)", c, re.S | re.M)
        if not m:
            return None
        tags = re.findall(r"\[([^\]]*)\]", m.group(1))
        return {ac for tag in tags for ac in re.findall(r"\bAC\d+\b", tag)}


def split_list(value):
    return [v.strip() for v in value.split(",") if v.strip() and v.strip() != "-"]


def parse_front(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return None, text
    fields = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]  # `title: "API: logowanie"`
            fields[key.strip()] = value
    return fields, m.group(2)


def load_tickets(errors):
    tickets = []
    for path in sorted(TICKETS.glob("T-*.md")):
        fields, body = parse_front(path.read_text(encoding="utf-8"))
        if fields is None:
            errors.append(f"{path.name}: brak front-matter (---)")
            continue
        tickets.append(Ticket(path, fields, body))
    return tickets


def load_questions(errors):
    if not QUESTIONS.exists():
        errors.append("docs/QUESTIONS.md: brak pliku")
        return []
    text = re.sub(r"<!--.*?-->", "", QUESTIONS.read_text(encoding="utf-8"), flags=re.S)
    for line in text.splitlines():
        if re.match(r"#+ *Q-", line) and not Q_HEADER.match(line):
            errors.append(f"QUESTIONS.md: nieczytelny nagłówek pytania `{line.strip()}` (wzór: `## Q-001 — Tytuł`)")
    parts = Q_HEADER.split(text)
    questions = []
    for i in range(1, len(parts), 3):
        qid, title, rest = parts[i], parts[i + 1], parts[i + 2]
        fields = dict(re.findall(r"^- (\w+): ?(.*)$", rest, re.M))
        questions.append({"id": qid, "title": title.strip(), "fields": fields})
    return questions


def open_blockers(questions):
    """ticket id -> lista otwartych pytań, które go blokują"""
    blockers = {}
    for q in questions:
        if q["fields"].get("status") == "open":
            for tid in split_list(q["fields"].get("blokuje", "")):
                blockers.setdefault(tid, []).append(q["id"])
    return blockers


def check_questions(questions, ticket_ids, errors):
    seen = set()
    for q in questions:
        qid, f = q["id"], q["fields"]
        if qid in seen:
            errors.append(f"QUESTIONS.md: zduplikowane {qid}")
        seen.add(qid)
        status = f.get("status")
        if status not in ("open", "resolved"):
            errors.append(f"QUESTIONS.md {qid}: status musi być open|resolved")
        if "blokuje" not in f:
            errors.append(f"QUESTIONS.md {qid}: brak pola `blokuje` (ID ticketów lub `-`)")
        for tid in split_list(f.get("blokuje", "")):
            if tid not in ticket_ids:
                errors.append(f"QUESTIONS.md {qid}: blokuje nieistniejący ticket {tid}")
        if status == "resolved" and not f.get("odpowiedź", "").strip():
            errors.append(f"QUESTIONS.md {qid}: resolved bez `odpowiedź`")


def check_ticket(t, tickets_by_id, blockers, errors):
    name = t.path.name

    def err(msg):
        errors.append(f"{name}: {msg}")

    for key in ("id", "title", "status", "rank"):
        if not t.fields.get(key):
            err(f"brak pola `{key}`")
    if t.id and not TICKET_ID.match(t.id):
        err(f"id `{t.id}` nie pasuje do T-<liczba>")
    if t.id and not name.startswith(t.id + "-"):
        err(f"nazwa pliku musi zaczynać się od `{t.id}-`")
    if t.status and t.status not in STATUSES:
        err(f"status `{t.status}` spoza {STATUSES}")
    if t.kind not in KINDS:
        err(f"kind `{t.kind}` spoza {KINDS}")
    if t.fields.get("rank") and t.rank == float("inf"):
        err("rank musi być liczbą")
    for dep in t.depends:
        if dep not in tickets_by_id:
            err(f"depends: nieistniejący ticket {dep}")
        elif tickets_by_id[dep].status == "dropped" and t.status not in ("done", "dropped"):
            err(f"depends: {dep} jest dropped — usuń zależność albo wskaż ticket zastępczy")
    spec = t.fields.get("spec", "")
    if spec and not (ROOT / spec).exists():
        err(f"spec `{spec}` nie istnieje")

    if t.status in ("ready", "in-progress", "done"):
        left = placeholders(t.body)
        if left:
            err(f"niewypełnione miejsca z szablonu ({len(left)}), np. `{left[0]}` — uzupełnij albo usuń")
        a = t.layer("A")
        if a is None:
            err("brak warstwy `# A. …`")
        else:
            for section in ("Cel", "Zakres", "Akceptacja"):
                if not re.search(rf"^## {section}\b", a, re.M):
                    err(f"w A brak sekcji `## {section}`")
        criteria = t.criteria()
        if not criteria:
            err("brak kryteriów akceptacji w formie `- [ ] AC1: …`")
        if not split_list(t.fields.get("allow", "")):
            err("brak `allow` (scope guard: globy plików, które wolno zmieniać)")
        if t.kind == "logic":
            c = t.layer("C")
            if c is None:
                err("kind: logic wymaga warstwy `# C. …`")
            else:
                covered = t.covered_criteria()
                if covered is None:
                    err("w C brak sekcji `## Scenariusze`")
                else:
                    missing = [ac for _, ac in criteria if ac not in covered]
                    if missing:
                        err(f"scenariusze C nie pokrywają: {', '.join(missing)} (oznacz scenariusz jako `[ACn]`)")
        if t.status in ("ready",) and t.id in blockers:
            err(f"ready, ale blokują go otwarte pytania: {', '.join(blockers[t.id])}")
    if t.status in ("in-progress", "done"):
        for dep in t.depends:
            if dep in tickets_by_id and tickets_by_id[dep].status != "done":
                err(f"{t.status}, ale zależność {dep} nie jest done")
    if t.status == "done":
        open_acs = [ac for mark, ac in t.criteria() if mark == " "]
        if open_acs:
            err(f"done, ale niezaznaczone kryteria: {', '.join(open_acs)}")


PLACEHOLDER_PREFIX = re.compile(r"^(?:[-*]|\d+\.)?\s*(?:\[[ xX]\]\s*)?(?:\[[^\]]*\]\s*)?(?:AC\d+:\s*)?(?:\*\*[^*]+\*\*\s*)?")


def placeholders(body):
    """Linie, których treść to `...` z szablonu (np. `- ...`, `- [ ] AC2: ...`, `1. [AC1] ...`, `- **In:** ...`)."""
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    out = []
    for line in body.splitlines():
        s = line.strip()
        if s and PLACEHOLDER_PREFIX.sub("", s, count=1).startswith(("...", "…")):
            out.append(s)
    return out


def find_cycles(tickets_by_id, errors):
    state = {}

    def visit(tid, trail):
        if state.get(tid) == 1:
            errors.append("zależności tworzą cykl: " + " → ".join(trail + [tid]))
            return
        if state.get(tid) == 2 or tid not in tickets_by_id:
            return
        state[tid] = 1
        for dep in tickets_by_id[tid].depends:
            visit(dep, trail + [tid])
        state[tid] = 2

    for tid in tickets_by_id:
        visit(tid, [])


def next_ticket(tickets, blockers):
    by_id = {t.id: t for t in tickets}
    in_progress = sorted((t for t in tickets if t.status == "in-progress"), key=lambda t: (t.rank, t.id))
    if in_progress:
        return in_progress[0]
    ready = [
        t for t in tickets
        if t.status == "ready"
        and t.id not in blockers
        and all(by_id.get(d) and by_id[d].status == "done" for d in t.depends)
    ]
    return min(ready, key=lambda t: (t.rank, t.id)) if ready else None


def render_backlog(tickets, blockers):
    by_id = {t.id: t for t in tickets}
    nxt = next_ticket(tickets, blockers)

    def link(t):
        return f"[{t.id}](tickets/{t.path.name})"

    def waiting(t):
        parts = [d for d in t.depends if d in by_id and by_id[d].status != "done"]
        parts += blockers.get(t.id, [])
        return ", ".join(parts) if parts else ""

    def section(title, status, with_wait):
        rows = sorted((t for t in tickets if t.status == status), key=lambda t: (t.rank, t.id))
        out = [f"## {title}", ""]
        if not rows:
            return out + ["_brak_", ""]
        head = "| ID | Tytuł | Czeka na |" if with_wait else "| ID | Tytuł |"
        out += [head, "|---|---|---|" if with_wait else "|---|---|"]
        for t in rows:
            title = t.title.replace("|", "\\|")  # `|` w tytule rozbiłby tabelę
            cells = f"| {link(t)} | {title} |"
            out.append(cells + (f" {waiting(t)} |" if with_wait else ""))
        return out + [""]

    lines = [
        "# Backlog",
        "",
        "<!-- GENEROWANY przez tools/docs_check.py --write. Nie edytuj ręcznie; status zmieniasz w tickecie. -->",
        "",
        "**Następny:** " + (f"{link(nxt)} — {nxt.title}" if nxt else "brak ticketu `ready` do realizacji — napisz/zaakceptuj kolejny"),
        "",
    ]
    lines += section("W toku", "in-progress", False)
    lines += section("Gotowe (wg rank)", "ready", True)
    lines += section("Szkice (czekają na akceptację)", "draft", True)
    lines += section("Zrobione", "done", False)
    lines += section("Odrzucone", "dropped", False)
    return "\n".join(lines).rstrip() + "\n"


def collect(write=False):
    """Waliduje dokumentację. Błędy w trzech grupach:
    choice — mogą zmienić wybór kolejnego ticketu (blokują --next);
    drafts — szkice, czyli praca właściciela w toku (nie blokują --next ani hooka Stop);
    other  — zakończone/odrzucone tickety, STATE.md, BACKLOG.md (blokują hook Stop, nie --next)."""
    choice, drafts, other = [], [], []
    tickets = load_tickets(choice)
    questions = load_questions(choice)

    seen = {}
    for t in tickets:
        if t.id in seen:
            choice.append(f"zduplikowane id {t.id}: {seen[t.id]}, {t.path.name}")
        seen[t.id] = t.path.name
    by_id = {t.id: t for t in tickets}
    blockers = open_blockers(questions)

    check_questions(questions, set(by_id), choice)
    for t in tickets:
        # nieznany/pusty status traktujemy jak kandydata (np. literówka „Ready”)
        target = drafts if t.status == "draft" else other if t.status in ("done", "dropped") else choice
        check_ticket(t, by_id, blockers, target)
    find_cycles(by_id, choice)

    if STATE.exists():
        n = len(STATE.read_text(encoding="utf-8").splitlines())
        if n > MAX_STATE_LINES:
            other.append(f"STATE.md ma {n} linii (limit {MAX_STATE_LINES}) — opis działania należy do specu/kodu")
    else:
        other.append("docs/STATE.md: brak pliku")

    rendered = render_backlog(tickets, blockers)
    if write:
        BACKLOG.write_text(rendered, encoding="utf-8")
    elif not BACKLOG.exists() or BACKLOG.read_text(encoding="utf-8") != rendered:
        other.append("docs/BACKLOG.md nieaktualny — uruchom: python3 tools/docs_check.py --write")

    return SimpleNamespace(tickets=tickets, questions=questions, blockers=blockers,
                           choice=choice, drafts=drafts, other=other)


def slugify(title, limit=40):
    s = unicodedata.normalize("NFKD", title.replace("ł", "l").replace("Ł", "L"))
    s = re.sub(r"[^a-z0-9]+", "-", s.encode("ascii", "ignore").decode().lower()).strip("-")
    if len(s) > limit:
        s = s[:limit].rsplit("-", 1)[0]
    return s or "ticket"


def new_ticket(title):
    """Szkic z szablonu: kolejne T-NNN (ID nie wracają, liczą się też dropped), rank za ostatnim ticketem."""
    tickets = load_tickets([])
    nums = [int(t.id[2:]) for t in tickets if TICKET_ID.match(t.id)]
    nums += [int(m.group(1)) for m in (re.match(r"T-(\d+)-", p.name) for p in TICKETS.glob("T-*.md")) if m]
    tid = f"T-{max(nums, default=0) + 1:03d}"
    text = TEMPLATE.read_text(encoding="utf-8").replace("T-000", tid)
    text = re.sub(r"^title:.*$", lambda m: f"title: {title}", text, count=1, flags=re.M)
    ranks = [t.rank for t in tickets if t.rank != float("inf")]
    if ranks:
        text = re.sub(r"^rank:.*$", f"rank: {int(max(ranks)) + 10}", text, count=1, flags=re.M)
    TICKETS.mkdir(parents=True, exist_ok=True)
    path = TICKETS / f"{tid}-{slugify(title)}.md"
    with open(path, "x", encoding="utf-8") as f:
        f.write(text)
    return path


def check_as_ready(arg):
    """Błędy ticketu, gdyby był `ready` — przed akceptacją szkicu."""
    m = re.match(r"(?:T-)?(\d+)$", arg)
    tickets = load_tickets([])
    t = next((t for t in tickets if m and TICKET_ID.match(t.id) and int(t.id[2:]) == int(m.group(1))), None)
    if t is None:
        return None, [f"brak ticketu {arg}"]
    if t.status not in ("in-progress", "done"):
        t.status = "ready"
    errors = []
    check_ticket(t, {x.id: x for x in tickets}, open_blockers(load_questions([])), errors)
    return t, errors


def main(argv):
    if "--check" in argv:
        i = argv.index("--check")
        arg = argv[i + 1] if i + 1 < len(argv) else ""
        if not arg or arg.startswith("--"):
            print("użycie: python3 tools/docs_check.py --check T-NNN")
            return 2
        t, errors = check_as_ready(arg)
        for e in errors:
            print(f"BŁĄD: {e}")
        if not errors:
            print(f"OK: {t.id} spełnia wymagania `ready`")
        return 1 if errors else 0

    if "--new" in argv:
        i = argv.index("--new")
        title = argv[i + 1].strip() if i + 1 < len(argv) else ""
        if not title or title.startswith("--") or "\n" in title:
            print('użycie: python3 tools/docs_check.py --new "Tytuł ticketu"')
            return 2
        try:
            path = new_ticket(title)
        except (OSError, ValueError) as e:
            print(f"BŁĄD: nie utworzono ticketu: {e}")
            return 1
        collect(write=True)
        print(path.relative_to(ROOT))
        return 0

    r = collect(write="--write" in argv)

    if "--next" in argv:
        for e in r.choice:
            print(f"BŁĄD: {e}")
        if r.choice:
            print("--next nie wskazuje ticketu, dopóki powyższe błędy nie zostaną poprawione.")
            return 1
        nxt = next_ticket(r.tickets, r.blockers)
        if nxt:
            print(f"{nxt.id} [{nxt.status}] {nxt.title}\n{nxt.path.relative_to(ROOT)}")
        else:
            print("brak ticketu ready do realizacji")
        soft = r.drafts + r.other
        if soft:
            print(f"UWAGA: dokumentacja ma błędy, które nie wpływają na wybór ticketu (liczba: {len(soft)}); szczegóły: python3 tools/docs_check.py")
        return 0 if nxt else 1

    tickets, questions = r.tickets, r.questions
    errors = r.choice + r.drafts + r.other
    for e in errors:
        print(f"BŁĄD: {e}")
    if not errors:
        print(f"OK: {len(tickets)} ticketów, {len(questions)} pytań")
    return 1 if errors else 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):  # UTF-8 niezależnie od kodowania systemu (Windows: cp1250)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
