from pathlib import Path
import pytest
from app.repositories.indexer import safe_workspace_path,index_repository

def test_workspace_escape_rejected(tmp_path):
    root=tmp_path/"root"; root.mkdir(); outside=tmp_path/"outside"; outside.mkdir()
    with pytest.raises(ValueError): safe_workspace_path(str(outside),root)
def test_index_skips_symlinks_and_secrets(tmp_path):
    (tmp_path/"app.py").write_text("print('hello')")
    (tmp_path/".env").write_text("SECRET=do-not-read")
    files=index_repository(tmp_path)
    assert [x["path"] for x in files]==["app.py"]
