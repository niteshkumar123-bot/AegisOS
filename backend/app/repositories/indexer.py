from pathlib import Path
import os

IGNORED={".git","node_modules",".venv","venv","dist","build","__pycache__",".next","vendor"}
ALLOWED={".py",".js",".jsx",".ts",".tsx",".java",".go",".rs",".c",".h",".cpp",".cs",".php",".rb",".html",".css",".json",".yaml",".yml",".toml",".md"}
MAX_FILES=1500; MAX_FILE_BYTES=200_000; MAX_TOTAL_BYTES=8_000_000

def safe_workspace_path(path: str, root: Path) -> Path:
    candidate=Path(path).expanduser()
    if not candidate.is_absolute(): candidate=root / candidate
    if candidate.is_symlink(): raise ValueError("Repository root cannot be a symlink")
    resolved=candidate.resolve()
    if resolved != root.resolve() and root.resolve() not in resolved.parents:
        raise ValueError("Workspace path must stay inside WORKSPACE_ROOT")
    if not resolved.exists() or not resolved.is_dir(): raise ValueError("Repository directory does not exist")
    return resolved

def index_repository(root: Path) -> list[dict]:
    files=[]; total=0
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORED and not (Path(current)/d).is_symlink()]
        for name in names:
            p=Path(current)/name
            if p.is_symlink() or p.suffix.lower() not in ALLOWED: continue
            try:
                size=p.stat().st_size
                if size > MAX_FILE_BYTES or total+size > MAX_TOTAL_BYTES: continue
                text=p.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError): continue
            if "\x00" in text: continue
            rel=p.relative_to(root).as_posix()
            # Ignore common secret/config files by name; never log source text.
            if name.lower() in {".env","id_rsa","credentials.json"}: continue
            files.append({"path":rel,"text":text,"size":size}); total+=size
            if len(files)>=MAX_FILES: return files
    return files

def retrieve_context(files: list[dict], issue: str, limit: int=24_000) -> str:
    terms={w.lower() for w in issue.split() if len(w)>2}
    ranked=[]
    for f in files:
        content=f["text"]
        score=sum(content.lower().count(t) for t in terms)+sum(1 for t in terms if t in f["path"].lower())
        ranked.append((score,f))
    ranked.sort(key=lambda x:(-x[0],x[1]["path"]))
    out=[]; used=0
    for _,f in ranked:
        chunk=f"FILE: {f['path']}\n{f['text'][:6000]}\n"
        if used+len(chunk)>limit: continue
        out.append(chunk); used+=len(chunk)
    return "\n".join(out)
