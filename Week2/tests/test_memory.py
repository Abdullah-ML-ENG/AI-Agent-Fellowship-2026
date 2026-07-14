from rag_application import save_chat_session, load_chat_session
import uuid

def test_memory_persistence():
    sid = str(uuid.uuid4())
    msgs = [{"role":"user","content":"Hello"}, {"role":"assistant","content":"Hi"}]
    save_chat_session(sid, msgs)
    loaded = load_chat_session(sid)
    assert loaded == msgs
