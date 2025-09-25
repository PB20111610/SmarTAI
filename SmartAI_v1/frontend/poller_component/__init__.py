# (这个文件的内容和上一回答中的完全一样)
import streamlit as st
import streamlit.components.v1 as components
import os

_RELEASE = True
if not _RELEASE:
    _component_func = components.declare_component(
        "poller_component",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend")
    _component_func = components.declare_component("poller_component", path=build_dir)


def poll_and_rerun(jobs_json: str, backend_url: str, key=None):
    component_value = _component_func(
        jobs_json=jobs_json, 
        backend_url=backend_url, 
        key=key, 
        default=None
    )

    if component_value:
        session_key = f"poller_last_completion_time_{key}"
        last_completion_time = st.session_state.get(session_key, None)

        if component_value.get("timestamp") != last_completion_time:
            st.session_state[session_key] = component_value.get("timestamp")
            st.rerun()
            
    return component_value