
import csv, os
COURSE_FILE = os.path.join('data', 'courses.csv')

def _load(path, key='course'):
    if not os.path.exists(path):
        return None, f'File not found: {path}'
    try:
        rows = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return None, 'CSV has no header row.'
            for r in reader:
                norm = { (k or '').strip().lower(): (v.strip() if isinstance(v, str) else v)
                         for k,v in r.items() }
                if norm.get(key):
                    rows.append(norm)
        if not rows:
            return None, 'No valid rows found.'
        return rows, None
    except Exception as e:
        return None, str(e)

def list_courses():
    rows, err = _load(COURSE_FILE, 'course')
    if err: return [], err
    out, seen = [], set()
    for r in rows:
        name = r.get('course', '')
        if not name: continue
        low = name.lower()
        if low not in seen:
            seen.add(low); out.append(name)
    return out, None

def course_details(name_low):
    rows, err = _load(COURSE_FILE, 'course')
    if err: return 'Course data error.', err
    q = (name_low or '').strip().lower()
    for r in rows:
        if (r.get('course','').lower()) == q:
            parts = []
            title = r.get('course')
            desc = r.get('description')
            skills = r.get('skills')
            subjects = r.get('subjects')
            if title: parts.append(f"*Course:* {title}")
            if desc: parts.append(f"*Summary:* {desc}")
            if skills: parts.append("*Skills:*\n- " + "\n- ".join([s.strip() for s in skills.split(';')]))
            if subjects: parts.append("*Subjects:*\n- " + "\n- ".join([s.strip() for s in subjects.split(';')]))
            return "\n".join(parts) or "No details available.", None
    return "Course not found.", None
