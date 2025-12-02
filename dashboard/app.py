import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page Configuration
st.set_page_config(page_title="Auto Agentic Testing", layout="wide")

# Paths to data files
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "apps" / "web_timer" / "tests"
DASHBOARD_DATA_PATH = DATA_DIR / "dashboard_data.json"
COVERAGE_DATA_PATH = BASE_DIR / "apps" / "web_timer" / "coverage.json"

def load_data():
    dashboard_data = {}
    coverage_data = {}
    prompts_data = {}
    
    if DASHBOARD_DATA_PATH.exists():
        with open(DASHBOARD_DATA_PATH, 'r') as f:
            dashboard_data = json.load(f)
            
    if COVERAGE_DATA_PATH.exists():
        with open(COVERAGE_DATA_PATH, 'r') as f:
            coverage_data = json.load(f)
    
    # Load prompts data (find the latest prompts file)
    prompts_files = list(DATA_DIR.glob("prompts_*.json"))
    if prompts_files:
        latest_prompts = max(prompts_files, key=lambda p: p.stat().st_mtime)
        with open(latest_prompts, 'r') as f:
            prompts_data = json.load(f)
            
    return dashboard_data, coverage_data, prompts_data

dashboard_data, coverage_data, prompts_data = load_data()

# Agent color scheme
AGENT_COLORS = {
    "identification_agent": {"color": "#4A90E2", "icon": "🔍", "name": "Test Identification Agent"},
    "implementation_agent": {"color": "#7B68EE", "icon": "🔧", "name": "Test Implementation Agent"},
    "implementation_agent_improvement": {"color": "#9370DB", "icon": "🔄", "name": "Test Improvement Agent"},
    "evaluation_agent": {"color": "#50C878", "icon": "📊", "name": "Evaluation Agent"},
    "syntax_fixer": {"color": "#FF6B6B", "icon": "🔨", "name": "Syntax Fixer"}
}

# Custom CSS for minimalistic design
st.markdown("""
<style>
    .agent-message {
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid;
    }
    .agent-header {
        font-weight: 600;
        font-size: 1.1em;
        margin-bottom: 10px;
    }
    .timestamp {
        font-size: 0.85em;
        color: #666;
        font-style: italic;
    }
    .response-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        max-height: 300px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Conversation", "Coverage"])

if page == "Conversation":
    st.title("🤖 Agent Conversation History")
    
    if not prompts_data or "prompts" not in prompts_data:
        st.info("No conversation history found. Please run the pipeline first.")
        st.stop()
    
    # Display metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Prompts", prompts_data.get("total_prompts", 0))
    with col2:
        st.metric("Model", prompts_data.get("model", "N/A"))
    with col3:
        st.metric("Run ID", prompts_data.get("run_id", "N/A"))
    
    st.markdown("---")
    
    # Display each prompt
    for idx, prompt in enumerate(prompts_data.get("prompts", [])):
        agent_name = prompt.get("agent", "unknown")
        agent_info = AGENT_COLORS.get(agent_name, {"color": "#999", "icon": "🤖", "name": agent_name.replace("_", " ").title()})
        
        with st.expander(f"{agent_info['icon']} {agent_info['name']} - {prompt.get('timestamp', 'N/A')}", expanded=(idx==0)):
            # Agent header with color
            st.markdown(f"""
            <div class="agent-message" style="border-left-color: {agent_info['color']}">
                <div class="agent-header" style="color: {agent_info['color']}">
                    {agent_info['icon']} {agent_info['name']}
                </div>
                <div class="timestamp">⏰ {prompt.get('timestamp', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # System Prompt
            with st.expander("📋 System Prompt", expanded=False):
                st.code(prompt.get("system_prompt", "N/A"), language="text")
            
            # User Prompt
            with st.expander("💬 User Prompt", expanded=False):
                st.code(prompt.get("user_prompt", "N/A"), language="text")
            
            # Response
            st.subheader("✨ Response")
            response = prompt.get("response", "N/A")
            
            # Try to parse as JSON for pretty formatting
            try:
                if response.startswith("```"):
                    # Extract JSON from markdown code fence
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response_json = json.loads(response)
                st.json(response_json)
            except:
                # If not JSON, display as code
                st.code(response, language="python")
            
            # Additional metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"**Model:** {prompt.get('model', 'N/A')}")
            with col2:
                is_mock = prompt.get("is_mock", False)
                st.caption(f"**Mock Response:** {'✅ Yes' if is_mock else '❌ No'}")

elif page == "Coverage":
    st.title("Coverage Dashboard")
    
    if not dashboard_data:
        st.error("No dashboard data found. Please run the pipeline first.")
        st.stop()

    # --- Top Metrics Cards ---
    metrics = dashboard_data.get("pipeline_metrics", [])
    latest_metrics = metrics[-1] if metrics else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        coverage_pct = latest_metrics.get("code_coverage_percentage", 0)
        st.metric(label="OVERALL COVERAGE", value=f"{coverage_pct:.0f}%", delta="Codebase Health")
        
    with col2:
        exec_time = latest_metrics.get("execution_time_seconds", 0)
        tests_total = latest_metrics.get("tests_total", 0)
        st.metric(label="PIPELINE VELOCITY", value=f"{exec_time:.2f}s", delta=f"{tests_total} Tests Run")

    st.markdown("---")

    # --- Charts Row 1: Pipeline Evolution & Security Distribution ---
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Pipeline Metrics Evolution")
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            
            # Create line chart with multiple axes or just multiple lines
            fig_evolution = go.Figure()
            
            fig_evolution.add_trace(go.Scatter(x=df_metrics['iteration'], y=df_metrics['execution_time_seconds'], name='Execution Time (s)', line=dict(color='red')))
            fig_evolution.add_trace(go.Scatter(x=df_metrics['iteration'], y=df_metrics['code_coverage_percentage'], name='Coverage (%)', line=dict(color='green')))
            fig_evolution.add_trace(go.Scatter(x=df_metrics['iteration'], y=df_metrics['security_issues_count'], name='Security Issues', line=dict(color='blue')))
            
            fig_evolution.update_layout(xaxis_title="Iteration", yaxis_title="Value", legend_title="Metrics")
            st.plotly_chart(fig_evolution, use_container_width=True)
        else:
            st.info("No evolution data available.")

    with col4:
        st.subheader("Security Vulnerabilities Distribution")
        security_dist = dashboard_data.get("security_distribution", [])
        if security_dist:
            df_sec = pd.DataFrame(security_dist)
            fig_sec = px.bar(df_sec, x='type', y='count', color='severity', 
                             color_discrete_map={'high': 'red', 'medium': 'orange', 'low': 'yellow'},
                             labels={'count': 'Count', 'type': 'Vulnerability Type'})
            st.plotly_chart(fig_sec, use_container_width=True)
        else:
            st.info("No security issues found.")

    st.markdown("---")

    # --- Charts Row 2: File Coverage & Test Outcomes ---
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("File Coverage")
        if coverage_data:
            files = coverage_data.get("files", {})
            for filename, file_data in files.items():
                pct = file_data.get("summary", {}).get("percent_covered", 0)
                st.write(f"**{filename}**")
                st.progress(int(pct) / 100)
                st.caption(f"{pct:.1f}%")
        else:
            st.info("No file coverage data available.")

    with col6:
        st.subheader("Test Outcomes")
        if latest_metrics:
            passed = latest_metrics.get("tests_passed", 0)
            failed = latest_metrics.get("tests_failed", 0)
            
            labels = ['Passing', 'Failing']
            values = [passed, failed]
            colors = ['#00CC96', '#EF553B'] # Green, Red
            
            fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=colors)])
            
            # Add center text
            pass_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
            fig_donut.update_layout(
                annotations=[dict(text=f"{pass_rate:.0f}%<br>PASS RATE", x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            st.plotly_chart(fig_donut, use_container_width=True)
            
            # Custom legend/stats below
            c1, c2 = st.columns(2)
            c1.metric("PASSING", passed)
            c2.metric("FAILING", failed)
        else:
            st.info("No test outcome data available.")
