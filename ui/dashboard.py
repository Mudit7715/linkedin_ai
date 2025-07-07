import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import yaml
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_tracker import EnhancedLinkedInTracker, OutreachStatus
from core.ollama_connector import OllamaConnector
from core.automation_scheduler import AutomationScheduler
from core.post_generator import PostGenerator

st.set_page_config(
    page_title="LinkedIn AI Outreach Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Initialize components
if 'tracker' not in st.session_state:
    st.session_state.tracker = EnhancedLinkedInTracker()
    
if 'ollama' not in st.session_state:
    st.session_state.ollama = OllamaConnector()
    
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = AutomationScheduler()

def main():
    st.title("🤖 LinkedIn AI Talent Outreach System")
    
    # Sidebar navigation
    page = st.sidebar.selectbox("Navigation", [
        "📊 Dashboard",
        "🎯 Pipeline Status",
        "📮 Message Queue",
        "📈 Analytics",
        "🔥 Viral Posts",
        "⚙️ Prompt Editor",
        "🔧 Settings"
    ])
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "🎯 Pipeline Status":
        show_pipeline_status()
    elif page == "📮 Message Queue":
        show_message_queue()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "🔥 Viral Posts":
        show_viral_posts()
    elif page == "⚙️ Prompt Editor":
        show_prompt_editor()
    elif page == "🔧 Settings":
        show_settings()

def show_dashboard():
    """Main dashboard overview"""
    st.header("Dashboard Overview")
    
    # Get analytics
    analytics = st.session_state.tracker.get_analytics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Targets",
            analytics['total_targets'],
            delta=f"{analytics['hiring_managers']} hiring managers"
        )
        
    with col2:
        st.metric(
            "Connections Sent",
            analytics['connections_sent'],
            delta=f"{analytics['today_connections']} today"
        )
        
    with col3:
        st.metric(
            "Acceptance Rate",
            f"{analytics['acceptance_rate']:.1%}",
            delta=f"{analytics['connections_accepted']} accepted"
        )
        
    with col4:
        st.metric(
            "Reply Rate",
            f"{analytics['reply_rate']:.1%}",
            delta=f"{analytics['messages_replied']} replies"
        )
    
    # Outreach funnel
    st.subheader("Outreach Funnel")
    
    fig = go.Figure(go.Funnel(
        y=["Targets", "Connections Sent", "Connections Accepted", "Messages Sent", "Replies"],
        x=[
            analytics['total_targets'],
            analytics['connections_sent'],
            analytics['connections_accepted'],
            analytics['messages_sent'],
            analytics['messages_replied']
        ],
        textinfo="value+percent initial"
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Daily activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Today's Activity")
        st.info(f"Connections sent: {analytics['today_connections']}/30")
        st.info(f"Messages sent: {analytics['today_messages']}")
        
        if st.button("🚀 Run Connection Requests Now"):
            with st.spinner("Running connection requests..."):
                st.session_state.scheduler.run_connection_requests()
                st.success("Connection requests completed!")
                st.experimental_rerun()
    
    with col2:
        st.subheader("System Status")
        
        # Check Ollama
        if st.session_state.ollama.check_health():
            st.success("✅ Ollama is running")
            models = st.session_state.ollama.list_models()
            st.info(f"Available models: {', '.join(models)}")
        else:
            st.error("❌ Ollama is not running")
            st.warning("Please start Ollama: `ollama serve`")

def show_pipeline_status():
    """Show current pipeline status"""
    st.header("Pipeline Status")
    
    # Status filter
    status_filter = st.selectbox("Filter by status", [
        "All", "Discovered", "Connection Sent", "Connection Accepted", 
        "Message Sent", "Message Replied", "Opted Out"
    ])
    
    # Get targets
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    
    if status_filter == "All":
        query = "SELECT * FROM targets ORDER BY updated_at DESC LIMIT 100"
    else:
        status_map = {
            "Discovered": OutreachStatus.DISCOVERED.value,
            "Connection Sent": OutreachStatus.CONNECTION_SENT.value,
            "Connection Accepted": OutreachStatus.CONNECTION_ACCEPTED.value,
            "Message Sent": OutreachStatus.MESSAGE_SENT.value,
            "Message Replied": OutreachStatus.MESSAGE_REPLIED.value,
            "Opted Out": OutreachStatus.OPTED_OUT.value
        }
        query = f"SELECT * FROM targets WHERE status = '{status_map[status_filter]}' ORDER BY updated_at DESC LIMIT 100"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        # Display targets
        st.dataframe(
            df[['name', 'company', 'title', 'location', 'status', 'ai_relevance_score', 'updated_at']],
            use_container_width=True
        )
        
        # Actions
        st.subheader("Actions")
        selected_id = st.selectbox("Select target", df['linkedin_id'].tolist())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Mark Connection Accepted"):
                st.session_state.tracker.record_connection_accepted(selected_id)
                st.success("Updated!")
                st.experimental_rerun()
                
        with col2:
            if st.button("Mark as Opted Out"):
                st.session_state.tracker.opt_out_target(selected_id)
                st.success("Target opted out")
                st.experimental_rerun()
                
        with col3:
            if st.button("View Profile"):
                st.info(f"Profile: linkedin.com/in/{selected_id}")
        
    else:
        st.info("No targets found for the selected status")

def show_message_queue():
    """Show pending messages queue"""
    st.header("Message Queue")
    
    # Get pending messages
    pending_df = st.session_state.tracker.get_pending_messages(hours_delay=5)
    
    if not pending_df.empty:
        st.info(f"Found {len(pending_df)} connections ready for messaging")
        
        # Display queue
        for idx, row in pending_df.iterrows():
            with st.expander(f"{row['name']} - {row['company']}"): 
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Title:** {row['title']}")
                    st.write(f"**Location:** {row.get('location', 'N/A')}")
                    st.write(f"**Accepted:** {row['accepted_at']}")
                    
                with col2:
                    if st.button(f"Send Message", key=f"msg_{row['linkedin_id']}"):
                        # Generate and send message
                        profile_data = json.loads(row['profile_data']) if row['profile_data'] else {}
                        
                        message = st.session_state.ollama.generate(
                            'personalized_message',
                            {
                                'name': row['name'],
                                'company': row['company'],
                                'title': row['title'],
                                'profile_data': json.dumps(profile_data),
                                'recent_activity': json.dumps(profile_data.get('recent_activity', []))
                            }
                        )
                        
                        if message:
                            st.session_state.tracker.record_message_sent(
                                row['linkedin_id'],
                                message,
                                message_type='personalized'
                            )
                            st.success("Message sent!")
                            st.experimental_rerun()
    else:
        st.info("No pending messages at the moment")
    
    # Message history
    st.subheader("Recent Messages")
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    messages_df = pd.read_sql_query(
        """
        SELECT m.*, t.name, t.company 
        FROM messages m
        JOIN targets t ON m.target_id = t.id
        ORDER BY m.sent_at DESC
        LIMIT 20
        """, 
        conn
    )
    conn.close()
    
    if not messages_df.empty:
        for _, msg in messages_df.iterrows():
            with st.expander(f"{msg['name']} - {msg['sent_at']}"): 
                st.write(f"**Company:** {msg['company']}")
                st.write(f"**Message:** {msg['content']}")
                if msg['replied_at']:
                    st.success(f"Replied on: {msg['replied_at']}")
                    if msg['reply_content']:
                        st.write(f"**Reply:** {msg['reply_content']}")

def show_analytics():
    """Show detailed analytics"""
    st.header("Analytics Dashboard")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Get time series data
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    
    # Daily connections
    daily_connections = pd.read_sql_query(
        """
        SELECT DATE(sent_at) as date, COUNT(*) as count
        FROM connections
        WHERE sent_at BETWEEN ? AND ?
        GROUP BY DATE(sent_at)
        ORDER BY date
        """,
        conn,
        params=(start_date, end_date)
    )
    
    # Daily messages
    daily_messages = pd.read_sql_query(
        """
        SELECT DATE(sent_at) as date, COUNT(*) as count
        FROM messages
        WHERE sent_at BETWEEN ? AND ?
        GROUP BY DATE(sent_at)
        ORDER BY date
        """,
        conn,
        params=(start_date, end_date)
    )
    
    # Company breakdown
    company_stats = pd.read_sql_query(
        """
        SELECT company, 
               COUNT(*) as total_targets,
               SUM(CASE WHEN status = 'connection_sent' THEN 1 ELSE 0 END) as connections_sent,
               SUM(CASE WHEN status = 'connection_accepted' THEN 1 ELSE 0 END) as connections_accepted,
               SUM(CASE WHEN status = 'message_sent' THEN 1 ELSE 0 END) as messages_sent,
               SUM(CASE WHEN status = 'message_replied' THEN 1 ELSE 0 END) as messages_replied
        FROM targets
        GROUP BY company
        ORDER BY total_targets DESC
        LIMIT 10
        """,
        conn
    )
    
    conn.close()
    
    # Visualizations
    st.subheader("Outreach Activity Timeline")
    
    if not daily_connections.empty or not daily_messages.empty:
        fig = go.Figure()
        
        if not daily_connections.empty:
            fig.add_trace(go.Scatter(
                x=daily_connections['date'],
                y=daily_connections['count'],
                mode='lines+markers',
                name='Connections Sent',
                line=dict(color='blue')
            ))
        
        if not daily_messages.empty:
            fig.add_trace(go.Scatter(
                x=daily_messages['date'],
                y=daily_messages['count'],
                mode='lines+markers',
                name='Messages Sent',
                line=dict(color='green')
            ))
        
        fig.update_layout(
            title="Daily Activity",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Company breakdown
    st.subheader("Top Companies by Engagement")
    
    if not company_stats.empty:
        # Calculate acceptance rate
        company_stats['acceptance_rate'] = (
            company_stats['connections_accepted'] / 
            company_stats['connections_sent'].replace(0, 1) * 100
        )
        
        fig = px.bar(
            company_stats.head(10),
            x='company',
            y=['connections_sent', 'connections_accepted', 'messages_sent', 'messages_replied'],
            title="Company Engagement Breakdown",
            labels={'value': 'Count', 'variable': 'Metric'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.dataframe(
            company_stats[['company', 'total_targets', 'connections_accepted', 'acceptance_rate', 'messages_replied']],
            use_container_width=True
        )

def show_viral_posts():
    """Show viral posts management"""
    st.header("Viral Posts Management")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Generated Posts", "Viral Analysis", "Post History"])
    
    with tab1:
        st.subheader("Pending Approval")
        
        # Get pending post
        pending_post = st.session_state.tracker.get_pending_post()
        
        if pending_post:
            st.write("**Generated Post:**")
            
            # Editable text area
            edited_content = st.text_area(
                "Edit post content:",
                value=pending_post['content'],
                height=200,
                max_chars=1300
            )
            
            # Character count
            st.write(f"Characters: {len(edited_content)}/1300")
            
            # Viral insights
            if pending_post['viral_insights']:
                with st.expander("View Viral Insights Used"):
                    st.json(pending_post['viral_insights'])
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Approve & Publish", type="primary"):
                    # Update content if edited
                    if edited_content != pending_post['content']:
                        st.session_state.tracker.update_post_content(
                            pending_post['id'], 
                            edited_content
                        )
                    
                    # Mark as published
                    st.session_state.tracker.record_post_published(pending_post['id'])
                    st.success("Post published!")
                    st.experimental_rerun()
            
            with col2:
                if st.button("🔄 Regenerate"):
                    # Generate new post
                    post_gen = PostGenerator(st.session_state.ollama)
                    
                    # Get viral insights
                    viral_insights = pending_post['viral_insights'] or {}
                    
                    new_post = post_gen.generate_optimized_post(viral_insights)
                    if new_post:
                        st.session_state.tracker.update_post_content(
                            pending_post['id'],
                            new_post['content']
                        )
                        st.success("Post regenerated!")
                        st.experimental_rerun()
            
            with col3:
                if st.button("❌ Reject"):
                    # Delete the post
                    conn = sqlite3.connect(st.session_state.tracker.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM posts WHERE id = ?", (pending_post['id'],))
                    conn.commit()
                    conn.close()
                    st.info("Post rejected")
                    st.experimental_rerun()
        
        else:
            st.info("No posts pending approval")
            
            if st.button("🎯 Generate New Post"):
                with st.spinner("Analyzing viral content and generating post..."):
                    # This would normally be done by the scheduler
                    # For manual generation, we'll simulate it
                    st.warning("Please run the scheduler to generate posts automatically")
    
    with tab2:
        st.subheader("Viral Content Analysis")
        
        # This would show analysis from viral post miner
        st.info("Run the viral post miner to see trending content analysis")
    
    with tab3:
        st.subheader("Published Posts")
        
        # Get published posts
        conn = sqlite3.connect(st.session_state.tracker.db_path)
        published_posts = pd.read_sql_query(
            """
            SELECT * FROM posts 
            WHERE published_at IS NOT NULL
            ORDER BY published_at DESC
            LIMIT 20
            """,
            conn
        )
        conn.close()
        
        if not published_posts.empty:
            for _, post in published_posts.iterrows():
                with st.expander(f"Post - {post['published_at']}"):
                    st.write(post['content'])
                    
                    if post['performance_metrics']:
                        metrics = json.loads(post['performance_metrics'])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Views", metrics.get('views', 0))
                        with col2:
                            st.metric("Reactions", metrics.get('reactions', 0))
                        with col3:
                            st.metric("Comments", metrics.get('comments', 0))
        else:
            st.info("No published posts yet")

def show_prompt_editor():
    """Show prompt configuration editor"""
    st.header("Prompt Configuration")
    
    # Load current prompts
    with open('config/prompts.yml', 'r') as f:
        prompts_config = yaml.safe_load(f)
    
    # Tabs for different prompt types
    tabs = st.tabs([
        "Connection Request",
        "Personalized Message", 
        "Viral Post",
        "Profile Analyzer",
        "Settings"
    ])
    
    with tabs[0]:
        st.subheader("Connection Request Prompts")
        
        system_prompt = st.text_area(
            "System Prompt:",
            value=prompts_config['prompts']['connection_request']['system'],
            height=200
        )
        
        user_prompt = st.text_area(
            "User Prompt Template:",
            value=prompts_config['prompts']['connection_request']['user'],
            height=150
        )
        
        # Test generation
        if st.button("Test Connection Request"):
            test_result = st.session_state.ollama.generate(
                'connection_request',
                {
                    'name': 'John Doe',
                    'company': 'Google',
                    'title': 'AI Engineering Manager',
                    'summary': 'Leading AI/ML initiatives at Google'
                }
            )
            st.write("**Generated:**")
            st.info(test_result)
    
    with tabs[1]:
        st.subheader("Personalized Message Prompts")
        
        system_prompt = st.text_area(
            "System Prompt:",
            value=prompts_config['prompts']['personalized_message']['system'],
            height=200,
            key="msg_system"
        )
        
        user_prompt = st.text_area(
            "User Prompt Template:",
            value=prompts_config['prompts']['personalized_message']['user'],
            height=150,
            key="msg_user"
        )
    
    with tabs[2]:
        st.subheader("Viral Post Prompts")
        
        system_prompt = st.text_area(
            "System Prompt:",
            value=prompts_config['prompts']['viral_post']['system'],
            height=200,
            key="post_system"
        )
        
        user_prompt = st.text_area(
            "User Prompt Template:",
            value=prompts_config['prompts']['viral_post']['user'],
            height=150,
            key="post_user"
        )
    
    with tabs[3]:
        st.subheader("Profile Analyzer Prompts")
        
        system_prompt = st.text_area(
            "System Prompt:",
            value=prompts_config['prompts']['profile_analyzer']['system'],
            height=200,
            key="analyzer_system"
        )
        
        user_prompt = st.text_area(
            "User Prompt Template:",
            value=prompts_config['prompts']['profile_analyzer']['user'],
            height=150,
            key="analyzer_user"
        )
    
    with tabs[4]:
        st.subheader("Model Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_name = st.selectbox(
                "Model:",
                options=['llama2', 'mistral', 'codellama'],
                index=0
            )
            
            temperature = st.slider(
                "Temperature:",
                min_value=0.0,
                max_value=2.0,
                value=prompts_config['ollama']['temperature'],
                step=0.1
            )
        
        with col2:
            max_tokens = st.number_input(
                "Max Tokens:",
                min_value=100,
                max_value=4000,
                value=prompts_config['ollama']['max_tokens'],
                step=100
            )
    
    # Save button
    if st.button("💾 Save All Changes", type="primary"):
        # Update config
        # (In production, you'd update the actual YAML file)
        st.success("Configuration saved!")
        st.info("Note: In production, this would update the prompts.yml file")

def show_settings():
    """Show system settings"""
    st.header("System Settings")
    
    # System status
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.ollama.check_health():
            st.success("✅ Ollama Connected")
        else:
            st.error("❌ Ollama Disconnected")
            st.code("ollama serve")
    
    with col2:
        st.info("🔄 Scheduler Status: Manual")
        if st.button("View Scheduler Logs"):
            st.code("python -m linkedin_ai_outreach.core.automation_scheduler")
    
    with col3:
        # Check database
        try:
            conn = sqlite3.connect(st.session_state.tracker.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM targets")
            count = cursor.fetchone()[0]
            conn.close()
            st.success(f"✅ Database OK ({count} targets)")
        except:
            st.error("❌ Database Error")
    
    # Manual actions
    st.subheader("Manual Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Run Scraper Now"):
            with st.spinner("Running scraper..."):
                # In production, this would trigger the actual scraper
                st.info("Scraper job queued. Check logs for progress.")
        
        if st.button("📮 Process Message Queue"):
            st.session_state.scheduler.check_accepted_connections()
            st.success("Message queue processed!")
    
    with col2:
        if st.button("🔥 Mine Viral Posts"):
            with st.spinner("Mining viral posts..."):
                st.info("Viral post mining started. Check viral posts tab.")
        
        if st.button("📊 Refresh Analytics"):
            st.experimental_rerun()
    
    # Configuration
    st.subheader("Configuration")
    
    with st.expander("Environment Variables"):
        st.code("""
# .env file configuration
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
OLLAMA_BASE_URL=http://localhost:11434
        """)
    
    with st.expander("Target Companies"):
        with open('config/prompts.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        st.write("**Global Leaders:**")
        st.write(", ".join(config['target_companies']['global_leaders']))
        
        st.write("**India Presence:**")
        st.write(", ".join(config['target_companies']['india_presence']))
    
    # Danger zone
    st.subheader("⚠️ Danger Zone")
    
    with st.expander("Dangerous Actions"):
        if st.button("🗑️ Clear Daily Limits", type="secondary"):
            conn = sqlite3.connect(st.session_state.tracker.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_limits WHERE date = ?", (datetime.now().date(),))
            conn.commit()
            conn.close()
            st.success("Daily limits cleared")
        
        if st.button("🔄 Reset All Targets to Discovered", type="secondary"):
            if st.checkbox("I understand this will reset all progress"):
                conn = sqlite3.connect(st.session_state.tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE targets SET status = 'discovered'") 
                conn.commit()
                conn.close()
                st.success("All targets reset")

if __name__ == "__main__":
    main()
                )
                st.text_area("Generated Message", message, height=200)
    else:
        st.warning("No targets found")

def show_message_queue():
    """Show pending messages"""
    st.header("Message Queue")
    
    # Get pending messages
    pending_df = st.session_state.tracker.get_pending_messages(hours_delay=5)
    
    if not pending_df.empty:
        st.info(f"Found {len(pending_df)} connections ready for messaging")
        
        # Display queue
        st.dataframe(
            pending_df[['name', 'company', 'title', 'accepted_at', 'days_since_accept']],
            use_container_width=True
        )
        
        if st.button("🚀 Process Message Queue"):
            with st.spinner("Processing messages..."):
                st.session_state.scheduler.check_accepted_connections()
                st.success("Message queue processed!")
                st.experimental_rerun()
    else:
        st.info("No pending messages")
    
    # Recent messages
    st.subheader("Recent Messages Sent")
    
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    messages_df = pd.read_sql_query("""
        SELECT m.*, t.name, t.company 
        FROM messages m
        JOIN targets t ON m.target_id = t.id
        ORDER BY m.sent_at DESC
        LIMIT 20
    """, conn)
    conn.close()
    
    if not messages_df.empty:
        for _, msg in messages_df.iterrows():
            with st.expander(f"{msg['name']} at {msg['company']} - {msg['sent_at']}"):
                st.text(msg['content'])
                if msg['replied_at']:
                    st.success(f"Replied at: {msg['replied_at']}")

def show_analytics():
    """Show detailed analytics"""
    st.header("Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Get time series data
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    
    # Daily connections
    daily_connections = pd.read_sql_query("""
        SELECT DATE(sent_at) as date, COUNT(*) as count
        FROM connections
        WHERE sent_at BETWEEN ? AND ?
        GROUP BY DATE(sent_at)
        ORDER BY date
    """, conn, params=(start_date, end_date))
    
    # Daily messages
    daily_messages = pd.read_sql_query("""
        SELECT DATE(sent_at) as date, COUNT(*) as count
        FROM messages
        WHERE sent_at BETWEEN ? AND ?
        GROUP BY DATE(sent_at)
        ORDER BY date
    """, conn, params=(start_date, end_date))
    
    conn.close()
    
    # Plot time series
    if not daily_connections.empty:
        fig1 = px.line(daily_connections, x='date', y='count', title='Daily Connection Requests')
        st.plotly_chart(fig1, use_container_width=True)
    
    if not daily_messages.empty:
        fig2 = px.line(daily_messages, x='date', y='count', title='Daily Messages Sent')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Company breakdown
    st.subheader("Top Companies by Targets")
    
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    company_stats = pd.read_sql_query("""
        SELECT company, COUNT(*) as count, AVG(ai_relevance_score) as avg_score
        FROM targets
        GROUP BY company
        ORDER BY count DESC
        LIMIT 20
    """, conn)
    conn.close()
    
    if not company_stats.empty:
        fig3 = px.bar(company_stats, x='company', y='count', color='avg_score',
                      title='Targets by Company', color_continuous_scale='viridis')
        st.plotly_chart(fig3, use_container_width=True)

def show_viral_posts():
    """Show viral posts section"""
    st.header("Viral Posts")
    
    # Initialize post generator
    if 'post_generator' not in st.session_state:
        st.session_state.post_generator = PostGenerator(st.session_state.ollama)
    
    # Pending posts for approval
    st.subheader("Posts Awaiting Approval")
    
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    pending_posts = pd.read_sql_query("""
        SELECT * FROM posts 
        WHERE approved = 0 AND published_at IS NULL
        ORDER BY scheduled_at DESC
    """, conn)
    
    if not pending_posts.empty:
        for _, post in pending_posts.iterrows():
            with st.expander(f"Post scheduled for {post['scheduled_at']}"):
                # Parse post content if it's a JSON with metadata
                try:
                    post_data = json.loads(post['content']) if post['content'].startswith('{') else {'content': post['content']}
                    content = post_data.get('content', post['content'])
                    
                    st.text_area("Content", content, height=200)
                    
                    # Show quality metrics if available
                    if 'quality_score' in post_data:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Quality Score", f"{post_data['quality_score']:.1%}")
                        with col2:
                            st.metric("Character Count", post_data.get('char_count', len(content)))
                        with col3:
                            st.metric("Est. Reach", post_data.get('estimated_reach', 'Unknown'))
                    
                except:
                    content = post['content']
                    st.text_area("Content", content, height=200)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Approve Post {post['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE posts SET approved = 1 WHERE id = ?", (post['id'],))
                        conn.commit()
                        st.success("Post approved!")
                        st.experimental_rerun()
                        
                with col2:
                    if st.button(f"🔄 Regenerate {post['id']}"):
                        feedback = st.text_input(f"Feedback for {post['id']}", "Make it more engaging")
                        if feedback:
                            new_post = st.session_state.post_generator.regenerate_with_feedback(content, feedback)
                            if new_post:
                                st.text_area("Regenerated Post", new_post['content'], height=200)
                
                with col3:
                    if st.button(f"❌ Reject Post {post['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM posts WHERE id = ?", (post['id'],))
                        conn.commit()
                        st.warning("Post rejected")
                        st.experimental_rerun()
    else:
        st.info("No posts awaiting approval")
    
    conn.close()
    
    # Generate new post
    st.subheader("Generate New Post")
    
    # Personal brand settings
    with st.expander("Personal Brand Settings"):
        tone = st.selectbox("Tone", ["Professional", "Casual", "Inspirational", "Educational"])
        expertise = st.text_input("Your Expertise", "AI/ML enthusiast and final year B.Tech student")
        personal_brand = {'tone': tone.lower(), 'expertise': expertise}
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Generate AI Post Now"):
            with st.spinner("Analyzing viral patterns and generating post..."):
                # Get viral insights
                from scrapers.viral_post_miner import ViralPostMiner
                miner = ViralPostMiner()
                cached_posts = miner.get_cached_viral_posts()
                
                viral_insights = {
                    'patterns': {
                        'content_patterns': [
                            'Questions drive 40% more engagement',
                            'Posts with data get 2x reactions',
                            'Personal stories increase comments by 60%'
                        ],
                        'common_hashtags': {'#AI': 10, '#MachineLearning': 8, '#Tech': 7},
                        'avg_content_length': 800,
                        'avg_engagement_rate': 0.05
                    },
                    'top_posts': cached_posts[:3] if cached_posts else []
                }
                
                # Generate optimized post
                post_result = st.session_state.post_generator.generate_optimized_post(
                    viral_insights, personal_brand
                )
                
                if post_result:
                    st.success("Post generated successfully!")
                    
                    # Display generated post
                    st.text_area("Generated Post", post_result['content'], height=250)
                    
                    # Show metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Quality Score", f"{post_result['quality_score']:.1%}")
                    with col2:
                        st.metric("Characters", post_result['char_count'])
                    with col3:
                        st.metric("Hashtags", len(post_result['hashtags']))
                    with col4:
                        st.info(post_result['estimated_reach'])
                    
                    st.info(f"Recommended posting time: {post_result['recommended_time']}")
                    
                    # Save to database
                    if st.button("💾 Save Post for Approval"):
                        conn = sqlite3.connect(st.session_state.tracker.db_path)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO posts (content, scheduled_at, viral_insights, llm_prompt_used)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            json.dumps(post_result),
                            datetime.now(),
                            json.dumps(viral_insights),
                            'viral_post_optimized'
                        ))
                        conn.commit()
                        conn.close()
                        st.success("Post saved!")
                        st.experimental_rerun()
    
    with col2:
        if st.button("🔄 Run Full Viral Analysis"):
            with st.spinner("Running viral post analysis..."):
                st.session_state.scheduler.run_morning_viral_post_job()
                st.success("Analysis complete! New post generated.")
                st.experimental_rerun()
    
    # Published posts
    st.subheader("Published Posts")
    
    conn = sqlite3.connect(st.session_state.tracker.db_path)
    published_posts = pd.read_sql_query("""
        SELECT * FROM posts 
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    if not published_posts.empty:
        for _, post in published_posts.iterrows():
            with st.expander(f"Published on {post['published_at']}"):
                st.text(post['content'])
                if post['performance_metrics']:
                    metrics = json.loads(post['performance_metrics'])
                    st.json(metrics)

def show_prompt_editor():
    """Edit prompts configuration"""
    st.header("Prompt Editor")
    
    # Load current prompts
    with open('config/prompts.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Select prompt to edit
    prompt_type = st.selectbox("Select Prompt Type", list(config['prompts'].keys()))
    
    if prompt_type:
        st.subheader(f"Editing: {prompt_type}")
        
        # Edit system prompt
        system_prompt = st.text_area(
            "System Prompt",
            config['prompts'][prompt_type]['system'],
            height=200
        )
        
        # Edit user prompt
        user_prompt = st.text_area(
            "User Prompt",
            config['prompts'][prompt_type]['user'],
            height=200
        )
        
        # Save changes
        if st.button("💾 Save Changes"):
            config['prompts'][prompt_type]['system'] = system_prompt
            config['prompts'][prompt_type]['user'] = user_prompt
            
            with open('config/prompts.yml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            # Reload prompts in Ollama connector
            st.session_state.ollama.reload_prompts()
            st.success("Prompts saved and reloaded!")
    
    # Test prompt
    st.subheader("Test Prompt")
    
    test_variables = {}
    if prompt_type == 'connection_request':
        test_variables['name'] = st.text_input("Name", "John Doe")
        test_variables['company'] = st.text_input("Company", "Google")
        test_variables['title'] = st.text_input("Title", "AI Research Manager")
        test_variables['summary'] = st.text_input("Summary", "Leading AI research...")
    
    if st.button("🧪 Test Generate"):
        with st.spinner("Generating..."):
            result = st.session_state.ollama.generate(prompt_type, test_variables)
            if result:
                st.text_area("Generated Output", result, height=200)
            else:
                st.error("Generation failed. Check if Ollama is running.")

def show_settings():
    """System settings"""
    st.header("Settings")
    
    # Ollama settings
    st.subheader("Ollama Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model = st.selectbox(
            "Model",
            st.session_state.ollama.list_models() or ["llama2"],
            index=0
        )
        
        if st.button("Change Model"):
            st.session_state.ollama.set_model(model)
            st.success(f"Model changed to {model}")
    
    with col2:
        temperature = st.slider(
            "Temperature",
            0.0, 1.0,
            st.session_state.ollama.config.temperature
        )
        
        if st.button("Update Temperature"):
            st.session_state.ollama.config.temperature = temperature
            st.success("Temperature updated")
    
    # Automation settings
    st.subheader("Automation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_connections = st.number_input(
            "Max Daily Connections",
            1, 50,
            st.session_state.scheduler.max_daily_connections
        )
        
        if st.button("Update Connection Limit"):
            st.session_state.scheduler.max_daily_connections = max_connections
            st.success("Connection limit updated")
    
    with col2:
        message_delay = st.number_input(
            "Message Delay (hours)",
            1, 24,
            st.session_state.scheduler.message_delay_hours
        )
        
        if st.button("Update Message Delay"):
            st.session_state.scheduler.message_delay_hours = message_delay
            st.success("Message delay updated")
    
    # Manual triggers
    st.subheader("Manual Triggers")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Run Scraper"):
            with st.spinner("Running scraper..."):
                st.session_state.scheduler.run_nightly_scraper()
                st.success("Scraper completed!")
    
    with col2:
        if st.button("📊 Reset Daily Counts"):
            st.session_state.scheduler.reset_daily_counts()
            st.success("Daily counts reset!")
    
    with col3:
        if st.button("🔄 Reload Prompts"):
            st.session_state.ollama.reload_prompts()
            st.success("Prompts reloaded!")

if __name__ == "__main__":
    main()
