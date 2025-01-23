import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Helper Functions

def generate_task_id():
    """Generate a unique task ID using hexadecimal characters."""
    return ''.join(random.choices('0123456789ABCDEF', k=10))

def simulate_processing(size_gb):
    """Simulate task processing time by sleeping for 7 seconds per GB."""
    time.sleep(size_gb * 7)  # 7 seconds per GB

# Blockchain Simulation

class SolanaBlockchain:
    def __init__(self):
        """Initialize the blockchain ledger for token transactions."""
        self.ledger = {}

    def transfer_tokens(self, from_user, to_user, amount):
        """
        Simulate token transfer between users. 
        - Check if the sender has enough tokens.
        - Update token balances and ledger.
        """
        if from_user.tokens >= amount:
            from_user.tokens -= amount
            to_user.tokens += amount
            self.ledger[from_user.id] = self.ledger.get(from_user.id, []) + [f"Sent {amount} tokens"]
            self.ledger[to_user.id] = self.ledger.get(to_user.id, []) + [f"Received {amount} tokens"]
            return True
        return False

# User Classes

class User:
    def __init__(self, blockchain, initial_tokens):
        """Initialize a user with an ID, token balance, and blockchain reference."""
        self.id = generate_task_id()
        self.tokens = initial_tokens
        self.task_history = []
        self.blockchain = blockchain
        self.connected = False

class Client(User):
    def submit_task(self, size_gb, task_name):
        """
        Submit a computational task.
        - Check if the client has enough tokens.
        - Deduct the cost from the client's balance.
        - Create and return a new task object.
        """
        task_cost = size_gb * 10  # 10 tokens per GB
        if self.tokens >= task_cost:
            self.tokens -= task_cost
            task = {
                "id": generate_task_id(), 
                "name": task_name, 
                "size_gb": size_gb, 
                "status": "Pending", 
                "timestamp": datetime.now()
            }
            self.task_history.append(task)
            return task
        else:
            st.error("Insufficient tokens for this task.")
            return None

    def track_task(self, task_id):
        """Find and return a task by its ID from the client's task history."""
        for task in self.task_history:
            if task['id'] == task_id:
                return task
        return None

class Contributor(User):
    def accept_task(self, task):
        """
        Process a task:
        - Simulate processing time.
        - Calculate and add earnings to the contributor's balance.
        - Update task status to 'Completed'.
        """
        st.write(f"Processing task {task['id']}...")
        simulate_processing(task['size_gb'])
        earnings = task['size_gb'] * 9  # 9 tokens per GB, 1 for platform fee
        self.tokens += earnings
        task['status'] = "Completed"  # This updates the task status to 'Completed'
        task['completed_at'] = datetime.now()
        self.task_history.append({
            "id": task['id'], 
            "size_gb": task['size_gb'], 
            "earnings": earnings, 
            "completed_at": task['completed_at'],
            "status": "Paid" if task['status'] == "Completed" else "Escrow"  # Add status here
        })
        return earnings

# Main App

def main():
    st.set_page_config(page_title="Decentralized Compute Marketplace", layout="wide")
    
    # Header with logo next to the title
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image("./logo.png", width=100, use_container_width=False)
    with col2:
        st.title("Decentralized Compute Marketplace")

    # Sidebar for navigation with user icon and "PrototypeUser" text
    col1, col2 = st.sidebar.columns([1, 3])
    with col1:
        st.image("user-icon.png", width=20, use_container_width=False)
    with col2:
        st.markdown("<h3 style='margin-top: 0; margin-bottom: 0;'>PrototypeUser</h3>", unsafe_allow_html=True)
    st.sidebar.title("Welcome to the Compute Market!")
    st.sidebar.markdown("Navigate through the roles to explore the marketplace.")

    # Initialize session state for persistence across role changes
    if 'solana' not in st.session_state:
        st.session_state.solana = SolanaBlockchain()
        st.session_state.clients = [Client(st.session_state.solana, 70) for _ in range(5)]  # Simulate 5 clients
        st.session_state.contributors = [Contributor(st.session_state.solana, 50) for _ in range(10)]  # Simulate 10 contributors
        st.session_state.all_tasks = []
        st.session_state.escrow = 0.0  # Initialize escrow to 0
        st.session_state.platform_earnings = 0.0  # Initialize platform earnings to 0

    # Role selection
    role = st.sidebar.selectbox("Select your role", ["Client", "Contributor", "Admin"])

    if role == "Client":
        st.subheader("Client Dashboard")
        
        # Connection Status with wallet icon next to the text
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("Connect Wallet"):
                st.session_state.clients[0].connected = True
        with col2:
            if st.session_state.clients[0].connected:
                st.image("wallet-icon.png", width=30, use_container_width=False)
        with col3:
            if st.session_state.clients[0].connected:
                st.markdown("* **Wallet connected**")

        # Wallet stats at the top
        col1, col2, col3 = st.columns(3)
        col1.metric("Your Tokens", f"{st.session_state.clients[0].tokens:.2f}")
        col2.metric("Tasks Submitted", len(st.session_state.clients[0].task_history))
        col3.metric("Tokens in Escrow", f"{st.session_state.escrow:.2f}")
        
        # Task submission form for clients
        with st.form("submit_task"):
            task_name = st.text_input("Task Name:", "AI model training file")
            task_size = st.number_input("Enter task size (GB):", min_value=1.0, max_value=100.0, value=1.0, step=1.0)
            submit = st.form_submit_button("Submit Task")
        
            if submit:
                with st.spinner('Encrypting and submitting task...'):
                    task = st.session_state.clients[0].submit_task(task_size, task_name)
                    if task:
                        st.session_state.all_tasks.append(task)
                        st.session_state.escrow += task_size * 10  # Transfer to escrow
                        st.success(f"Task **{task['id']}** encrypted and submitted. Awaiting contributors.")
                        st.rerun()

        # Task tracking
        st.subheader("Task Tracking")
        if st.session_state.clients[0].task_history:
            selected_task = st.selectbox("Select a task to track:", [t['id'] for t in st.session_state.clients[0].task_history])
            task = st.session_state.clients[0].track_task(selected_task)
            if task:
                st.markdown(f"**Task ID:** {task['id']}")
                st.markdown(f"**Name:** {task['name']}")
                st.markdown(f"**Size:** {task['size_gb']} GB")
                st.markdown(f"**Status:** {task['status']}")
                
                if task['status'] == "Pending":
                    st.info("Task is still pending.")
                else:
                    st.success("Task completed!")
                    st.markdown(f"**Completed at:** {task['completed_at']}")
        else:
            st.info("No tasks to track yet.")

        # Task history display
        st.subheader("Task History")
        
        # Convert the task history to a DataFrame
        history_df = pd.DataFrame(st.session_state.clients[0].task_history)
        
        if not history_df.empty:
            # Custom styling to match the design
            styled_df = history_df.style.set_properties(**{
                'background-color': '#1a1a2e',  # Dark blue background
                'color': 'white',  # White text
                'border-color': '#4b4b62',  # Lighter border color for cells
                'padding': '10px'
            }).format({
                'id': lambda x: f'<span style="color: #fff;">#{x}</span>',
                'size_gb': lambda x: f'<span style="color: #fff;">{x} GB</span>',
                'status': lambda x: f'<span style="color: #fff; background-color: {"#00b8a9" if x == "Completed" else "#fca311"}; padding: 5px 10px; border-radius: 5px;">{x}</span>'
            }).hide()
        
            # Use st.markdown to display the HTML
            st.markdown(styled_df.to_html(), unsafe_allow_html=True)
        else:
            st.info("No task history to display.")

    elif role == "Contributor":
        st.subheader("Contributor Dashboard")

        # Connection Status with server icon next to the text
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("Connect to Server"):
                st.session_state.contributors[0].connected = True
        with col2:
            if st.session_state.contributors[0].connected:
                st.image("server-icon.png", width=30, use_container_width=False)
        with col3:
            if st.session_state.contributors[0].connected:
                st.markdown("* **Server connected**")

        # Wallet stats at the top
        col1, col2, col3 = st.columns(3)
        col1.metric("Your Tokens", f"{st.session_state.contributors[0].tokens:.2f}")
        col2.metric("Tasks Processed", len(st.session_state.contributors[0].task_history))
        col3.metric("Tokens in Escrow", f"{st.session_state.escrow:.2f}")
        
        # Display hardware specifications if connected
        if st.session_state.contributors[0].connected:
            st.markdown("### Available Resources")
            st.markdown("- **GPU:** NVIDIA RTX 3090")
            st.markdown("- **CPU:** AMD Ryzen 9 5950X")
            st.markdown("- **RAM:** 128GB DDR4")
            st.markdown("- **Storage:** 2TB NVMe SSD")

        # Task processing interface for contributors
        st.markdown("### Task Marketplace")
        
        with st.container():
            pending_tasks = [task for task in st.session_state.all_tasks if task['status'] == "Pending"]
            if pending_tasks:
                task_to_process = st.selectbox(
                    "Select task to process:", 
                    pending_tasks, 
                    format_func=lambda x: f"Task ID: {x['id']} - Name: {x['name']} - Size: {x['size_gb']} GB"
                )
                if st.button("Process Task"):
                    with st.spinner('Processing task...'):
                        simulate_processing(task_to_process['size_gb'])
                        
                        earnings = task_to_process['size_gb'] * 9  # 9 tokens per GB, 1 for platform fee
                        if st.session_state.escrow >= earnings:
                            for client in st.session_state.clients:
                                if client.tokens >= earnings:
                                    if st.session_state.solana.transfer_tokens(client, st.session_state.contributors[0], earnings):
                                        client.tokens -= earnings
                                        st.session_state.contributors[0].tokens += earnings
                                        st.session_state.escrow -= earnings  # Subtract from escrow
                                        break
                            else:
                                st.error("Error: Insufficient tokens in escrow to pay for this task.")
                        
                        # Platform fee
                        platform_fee = task_to_process['size_gb']  # 1 token per GB goes to platform
                        st.session_state.platform_earnings += platform_fee
                        st.session_state.escrow -= platform_fee  # Subtract platform fee from escrow
                        
                        # Update task status regardless of payment issues
                        task_to_process['status'] = "Completed"
                        task_to_process['completed_at'] = datetime.now()
                        st.session_state.contributors[0].accept_task(task_to_process)
                        
                        if st.session_state.escrow >= earnings:
                            st.success(f"Task processed successfully. Earnings of {earnings} tokens transferred from escrow to wallet.")
                        else:
                            st.warning("Task completed, but payment failed due to insufficient escrow.")
                        
                        # Update client's task history
                        client_task = st.session_state.clients[0].track_task(task_to_process['id'])
                        if client_task:
                            client_task['status'] = "Completed"
                            client_task['completed_at'] = datetime.now()
                        
                        # Remove processed task from available tasks
                        st.session_state.all_tasks = [t for t in st.session_state.all_tasks if t['id'] != task_to_process['id']]
                        st.rerun()
            else:
                st.info("No tasks available to process.")

        # Earnings History
        st.markdown("### Earnings History")
        earnings_df = pd.DataFrame(st.session_state.contributors[0].task_history)
        if not earnings_df.empty:
            # Custom styling for earnings history
            styled_earnings_df = earnings_df.style.set_properties(**{
                'background-color': '#1a1a2e',
                'color': 'white',
                'border-color': '#4b4b62',
                'padding': '10px'
            }).format({
                'id': lambda x: f'<span style="color: #fff;">#{x}</span>',
                'size_gb': lambda x: f'<span style="color: #fff;">{x} GB</span>',
                'earnings': lambda x: f'<span style="color: #fff;">{x:.2f}</span>',
                'completed_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S')
            }).apply(lambda x: ['background-color: #00b8a9' if x['status'] == 'Paid' else 'background-color: #fca311'], axis=1, subset=['status']).hide()
            
            # Use st.markdown to display the HTML
            st.markdown(styled_earnings_df.to_html(), unsafe_allow_html=True)
        else:
            st.info("No earnings history to display.")
    
    elif role == "Admin":
        st.subheader("Admin Dashboard")
        
        st.markdown("### Platform Statistics")
        total_tasks = len(st.session_state.all_tasks)
        total_tokens_in_escrow = st.session_state.escrow
        platform_earnings = st.session_state.platform_earnings
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", total_tasks)
        col2.metric("Tokens in Escrow", f"{total_tokens_in_escrow:.2f}")
        col3.metric("Platform Earnings", f"{platform_earnings:.2f}")
        
        # Pie Chart for Platform Earnings Breakdown
        st.markdown("### Platform Earnings Breakdown")
        labels = ['Client Earnings', 'Platform Fee', 'Contributor Earnings']
        values = [platform_earnings * 0.5, platform_earnings * 0.1, platform_earnings * 0.4]  # Example distribution
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
        fig.update_layout(title_text='Earnings Distribution', title_x=0.5)
        st.plotly_chart(fig)

        st.markdown("### Leaderboard")
        leaderboard = sorted(st.session_state.contributors, key=lambda x: sum(task['earnings'] for task in x.task_history), reverse=True)
        leaderboard_df = pd.DataFrame({
            'Contributor': [f"Contributor-{i+1}" for i in range(len(st.session_state.contributors))],
            'Total Earnings': [sum(task['earnings'] for task in c.task_history) for c in leaderboard],
            'Tasks Completed': [len(c.task_history) for c in leaderboard]
        })
        if not leaderboard_df.empty:
            st.dataframe(leaderboard_df)
        else:
            st.info("No leaderboard data available.")

    # This line should not be indented under any if block
    st.sidebar.markdown("**Note:** This is a simulation, not connected to actual blockchain or real-world data.")

if __name__ == "__main__":
    main()
