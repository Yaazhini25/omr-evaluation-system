# app.py
import streamlit as st
from omr_preprocessing import preprocess_omr
from omr_bubble_detection import extract_bubbles
from omr_scoring import calculate_score
from db_setup import init_db, save_results, get_all_results
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_donut_chart(data, title, colors=None):
    """
    Create a beautiful donut chart with custom styling
    """
    if colors is None:
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
    
    fig = go.Figure(data=[go.Pie(
        labels=data.index, 
        values=data.values,
        hole=0.5,
        marker_colors=colors[:len(data)],
        textinfo='label+percent+value',
        textfont_size=12,
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )])
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=18, color='#2E86C1')
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01
        ),
        margin=dict(t=50, b=10, l=10, r=120),
        height=400,
        font=dict(size=11)
    )
    
    return fig


def create_subject_wise_donut_charts(df, subject_names):
    """
    Create individual donut charts for each subject showing score distribution
    """
    # Calculate score ranges for better visualization
    score_ranges = ['0-5', '6-10', '11-15', '16-20']
    colors = ['#FF6B6B', '#FFA07A', '#98D8C8', '#4ECDC4']
    
    # Create subplots
    cols = min(3, len(subject_names))
    rows = (len(subject_names) + cols - 1) // cols
    
    fig = make_subplots(
        rows=rows, cols=cols,
        specs=[[{"type": "domain"}] * cols for _ in range(rows)],
        subplot_titles=subject_names,
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    for idx, subject in enumerate(subject_names):
        if subject in df.columns:
            scores = df[subject]
            
            # Categorize scores into ranges
            score_distribution = pd.cut(
                scores, 
                bins=[0, 5, 10, 15, 20], 
                labels=score_ranges, 
                include_lowest=True
            ).value_counts()
            
            row = idx // cols + 1
            col = idx % cols + 1
            
            fig.add_trace(
                go.Pie(
                    labels=score_distribution.index,
                    values=score_distribution.values,
                    hole=0.4,
                    marker_colors=colors,
                    textinfo='percent',
                    textfont_size=10,
                    name=subject
                ),
                row=row, col=col
            )
    
    fig.update_layout(
        title=dict(
            text="📊 Subject-wise Score Distribution",
            x=0.5,
            font=dict(size=20, color='#2E86C1')
        ),
        height=300 * rows,
        showlegend=True,
        font=dict(size=10)
    )
    
    return fig


def create_overall_performance_chart(df, subject_names):
    """
    Create overall performance visualization
    """
    if df.empty or 'Total' not in df.columns:
        return None
    
    # Total score distribution
    total_scores = df['Total']
    
    # Create score ranges for total (0-100)
    score_ranges = ['0-25', '26-50', '51-75', '76-100']
    colors = ['#FF6B6B', '#FFA07A', '#FFD93D', '#4ECDC4']
    
    total_distribution = pd.cut(
        total_scores,
        bins=[0, 25, 50, 75, 100],
        labels=score_ranges,
        include_lowest=True
    ).value_counts()
    
    fig = create_donut_chart(
        total_distribution,
        "🎯 Overall Performance Distribution (Total Scores)",
        colors
    )
    
    return fig


def create_subject_averages_chart(df, subject_names):
    """
    Create a bar chart showing average scores per subject
    """
    if df.empty:
        return None
    
    averages = []
    for subject in subject_names:
        if subject in df.columns:
            averages.append(df[subject].mean())
        else:
            averages.append(0)
    
    fig = go.Figure(data=[
        go.Bar(
            x=subject_names,
            y=averages,
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
            text=[f'{avg:.1f}' for avg in averages],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="📈 Average Scores by Subject",
            x=0.5,
            font=dict(size=18, color='#2E86C1')
        ),
        xaxis_title="Subjects",
        yaxis_title="Average Score",
        yaxis=dict(range=[0, 20]),
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return fig


def create_performance_metrics_cards(df, subject_names):
    """
    Create metric cards for key performance indicators
    """
    if df.empty:
        return
    
    # Calculate metrics
    total_students = len(df)
    avg_total = df['Total'].mean() if 'Total' in df.columns else 0
    max_score = df['Total'].max() if 'Total' in df.columns else 0
    min_score = df['Total'].min() if 'Total' in df.columns else 0
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Total Students",
            value=total_students,
            delta=f"+{total_students}" if total_students > 0 else None
        )
    
    with col2:
        st.metric(
            label="📊 Average Score",
            value=f"{avg_total:.1f}",
            delta=f"{avg_total:.1f}%" if avg_total > 0 else None
        )
    
    with col3:
        st.metric(
            label="🏆 Highest Score",
            value=max_score,
            delta=f"Max: {max_score}" if max_score > 0 else None
        )
    
    with col4:
        st.metric(
            label="📉 Lowest Score",
            value=min_score,
            delta=f"Min: {min_score}" if min_score >= 0 else None
        )


st.set_page_config(page_title="OMR Evaluation System", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .section-header {
        font-size: 1.5rem;
        color: #E74C3C;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #E74C3C;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🎯 Automated OMR Evaluation System</h1>', unsafe_allow_html=True)

# Initialize session state
if 'answer_key_loaded' not in st.session_state:
    st.session_state.answer_key_loaded = False
if 'answer_key' not in st.session_state:
    st.session_state.answer_key = None
if 'subject_names' not in st.session_state:
    st.session_state.subject_names = []

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    debug_mode = st.checkbox("🔍 Enable Debug Mode", value=False)
    show_charts = st.checkbox("📊 Show Detailed Charts", value=True)
    
    st.markdown("---")
    st.markdown("### 📋 Quick Guide")
    st.markdown("""
    1. Upload answer key Excel file
    2. Upload OMR sheet images
    3. Click 'Start Evaluation'
    4. View results and charts
    5. Download CSV reports
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="section-header">📋 Step 1: Upload Answer Key</div>', unsafe_allow_html=True)
    
    # Answer key upload section
    answer_file = st.file_uploader(
        "Upload Answer Key Excel File", 
        type=["xlsx", "xls"],
        help="Excel file should have subjects as columns and answers as rows"
    )
    
    if answer_file:
        try:
            df_key = pd.read_excel(answer_file, header=0)
            
            # Show the structure of uploaded file
            st.write("**📊 Answer Key Preview:**")
            st.dataframe(df_key.head(), use_container_width=True)
            
            # Get subject names and structure the answer key properly
            subject_names = [str(col) for col in df_key.columns.tolist()]
            
            # The Excel structure shows each column is a subject with 20 answers
            questions_per_subject = len(df_key)
            
            # Flatten the answer key properly - each column represents a subject
            answer_key_flat = []
            for subject_col in df_key.columns:
                subject_answers = df_key[subject_col].dropna().tolist()
                # Clean and convert each answer
                clean_answers = []
                for ans in subject_answers:
                    if isinstance(ans, str):
                        # Extract just the letter part (e.g., "1 - a" -> "a")
                        parts = ans.strip().split(' - ')
                        if len(parts) >= 2:
                            clean_answers.append(parts[1].strip())
                        else:
                            clean_answers.append(ans.strip())
                    else:
                        clean_answers.append(str(ans))
                answer_key_flat.extend(clean_answers)
            
            st.session_state.answer_key = answer_key_flat
            st.session_state.subject_names = subject_names
            st.session_state.answer_key_loaded = True
            
            st.markdown('<div class="success-box">✅ Answer key loaded successfully!</div>', unsafe_allow_html=True)
            st.info(f"**Subjects:** {', '.join(subject_names)}")
            st.info(f"**Questions per subject:** {questions_per_subject}")
            st.info(f"**Total questions:** {len(answer_key_flat)}")
            
            # Initialize database
            init_db(subject_names)
            
            if debug_mode:
                st.write("**🔍 Debug - Answer Key Sample:**", answer_key_flat[:10])
                
        except Exception as e:
            st.error(f"❌ Error loading answer key: {str(e)}")
            st.session_state.answer_key_loaded = False

with col2:
    st.markdown('<div class="section-header">📄 Step 2: Upload OMR Sheets</div>', unsafe_allow_html=True)
    
    # OMR sheets upload section
    uploaded_files = st.file_uploader(
        "Upload OMR Sheet Images", 
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload one or more OMR sheet images"
    )
    
    # Student name input
    student_name_input = st.text_input(
        "Student Name (optional)", 
        placeholder="Leave empty for auto-generated names"
    )

# Evaluation section
st.markdown('<div class="section-header">🔍 Step 3: Evaluate OMR Sheets</div>', unsafe_allow_html=True)

if st.button("🚀 Start Evaluation", type="primary", use_container_width=True):
    if not st.session_state.answer_key_loaded:
        st.error("❌ Please upload the answer key first!")
    elif not uploaded_files:
        st.error("❌ Please upload at least one OMR sheet!")
    else:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        total_files = len(uploaded_files)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing sheet {idx + 1} of {total_files}...")
            progress_bar.progress((idx) / total_files)
            
            # Create columns for each sheet
            with st.expander(f"📋 Sheet {idx + 1} - {uploaded_file.name}", expanded=(idx == 0)):
                sheet_col1, sheet_col2 = st.columns([1, 1])
                
                try:
                    with sheet_col1:
                        st.image(uploaded_file, caption=f"Original Sheet {idx+1}", use_container_width=True)
                    
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Preprocess image
                    thresh_img = preprocess_omr(uploaded_file)
                    
                    with sheet_col2:
                        st.image(thresh_img, caption="Processed Image", use_container_width=True)
                    
                    # Extract bubbles
                    student_answers = extract_bubbles(
                        thresh_img,
                        num_subjects=len(st.session_state.subject_names),
                        questions_per_subject=len(st.session_state.answer_key) // len(st.session_state.subject_names),
                        choices_per_question=4,  # A, B, C, D for Innomatics sheets
                        debug=debug_mode
                    )
                    
                    # Calculate scores
                    subject_scores, total_score = calculate_score(
                        student_answers, 
                        st.session_state.answer_key,
                        num_subjects=len(st.session_state.subject_names),
                        questions_per_subject=len(st.session_state.answer_key) // len(st.session_state.subject_names),
                        debug=debug_mode
                    )
                    
                    # Determine student name
                    if student_name_input.strip():
                        student_name = f"{student_name_input}_{idx+1}" if total_files > 1 else student_name_input
                    else:
                        student_name = f"Student_{idx+1}"
                    
                    # Save to database
                    save_results(student_name, subject_scores, total_score, st.session_state.subject_names)
                    
                    # Prepare result for display
                    result_dict = {"Student": student_name}
                    for i, subject in enumerate(st.session_state.subject_names):
                        result_dict[subject] = subject_scores[i]
                    result_dict["Total"] = total_score
                    all_results.append(result_dict)
                    
                    # Show individual result with mini chart
                    st.subheader(f"🎯 Results for {student_name}")
                    result_df = pd.DataFrame([result_dict])
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Individual student donut chart
                    if show_charts:
                        individual_scores = pd.Series(subject_scores, index=st.session_state.subject_names)
                        individual_chart = create_donut_chart(
                            individual_scores,
                            f"📊 {student_name}'s Subject Scores"
                        )
                        st.plotly_chart(individual_chart, use_container_width=True, key=f"individual_chart_{idx}_{student_name}")
                    
                    if debug_mode:
                        st.write("**🔍 Debug Info:**")
                        st.write(f"Detected answers: {student_answers[:20]}...")
                        st.write(f"Subject scores: {subject_scores}")
                        st.write(f"Total score: {total_score}")
                    
                except Exception as e:
                    st.error(f"❌ Error processing sheet {idx+1}: {str(e)}")
                    if debug_mode:
                        st.exception(e)
        
        # Update progress
        progress_bar.progress(1.0)
        status_text.text("✅ Evaluation completed!")
        
        if all_results:
            # Display summary results
            st.markdown('<div class="section-header">📊 Summary Results & Analytics</div>', unsafe_allow_html=True)
            
            summary_df = pd.DataFrame(all_results)
            
            # Performance metrics cards
            create_performance_metrics_cards(summary_df, st.session_state.subject_names)
            
            # Main results table
            st.subheader("📋 Detailed Results Table")
            st.dataframe(summary_df, use_container_width=True)
            
            # Download button
            csv_data = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name="omr_evaluation_results.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Charts section
            if show_charts:
                st.markdown('<div class="section-header">📈 Data Visualization</div>', unsafe_allow_html=True)
                
                # Create two columns for charts
                chart_col1, chart_col2 = st.columns([1, 1])
                
                with chart_col1:
                    # Overall performance donut chart
                    overall_chart = create_overall_performance_chart(summary_df, st.session_state.subject_names)
                    if overall_chart:
                        st.plotly_chart(overall_chart, use_container_width=True, key="current_overall_chart")
                    
                    # Subject averages bar chart
                    avg_chart = create_subject_averages_chart(summary_df, st.session_state.subject_names)
                    if avg_chart:
                        st.plotly_chart(avg_chart, use_container_width=True, key="current_avg_chart")
                
                with chart_col2:
                    # Subject-wise distribution charts
                    subject_charts = create_subject_wise_donut_charts(summary_df, st.session_state.subject_names)
                    if subject_charts:
                        st.plotly_chart(subject_charts, use_container_width=True, key="current_subject_charts")

# Show all previous results with charts
st.markdown('<div class="section-header">📋 Historical Results & Analytics</div>', unsafe_allow_html=True)
try:
    all_data, col_names = get_all_results()
    if all_data and len(all_data) > 0:
        df_all = pd.DataFrame(all_data, columns=col_names)
        
        # Filter out non-subject columns
        non_subject_cols = ['ID', 'Student', 'Total', 'Created_At']
        subject_cols = [col for col in df_all.columns if col not in non_subject_cols and col in st.session_state.subject_names]
        
        if subject_cols:
            # Performance metrics for all historical data
            st.subheader("📊 Historical Performance Metrics")
            create_performance_metrics_cards(df_all, subject_cols)
            
            # Charts for historical data
            if show_charts and not df_all.empty:
                hist_col1, hist_col2 = st.columns([1, 1])
                
                with hist_col1:
                    # Historical overall performance
                    hist_overall = create_overall_performance_chart(df_all, subject_cols)
                    if hist_overall:
                        st.plotly_chart(hist_overall, use_container_width=True, key="historical_overall_chart")
                
                with hist_col2:
                    # Historical subject averages
                    hist_avg = create_subject_averages_chart(df_all, subject_cols)
                    if hist_avg:
                        st.plotly_chart(hist_avg, use_container_width=True, key="historical_avg_chart")
                
                # Historical subject-wise distribution
                if len(subject_cols) > 0:
                    hist_subjects = create_subject_wise_donut_charts(df_all, subject_cols)
                    if hist_subjects:
                        st.plotly_chart(hist_subjects, use_container_width=True, key="historical_subject_charts")
        
        st.subheader("📋 All Historical Data")
        st.dataframe(df_all, use_container_width=True)
        
        # Download all results
        if not df_all.empty:
            all_csv_data = df_all.to_csv(index=False)
            st.download_button(
                label="📥 Download All Historical Results",
                data=all_csv_data,
                file_name="all_omr_results.csv",
                mime="text/csv"
            )
    else:
        st.info("📊 No previous results found. Complete some evaluations to see analytics here!")
except Exception as e:
    st.error(f"Error loading previous results: {str(e)}")

# Add helpful information
with st.expander("ℹ️ How to use this system & Chart Explanations"):
    st.markdown("""
    ### 📊 **Chart Guide:**
    
    **🍩 Donut Charts:**
    - **Individual Results**: Shows score distribution for each student
    - **Overall Performance**: Shows how students perform in different score ranges
    - **Subject-wise Distribution**: Shows score ranges across all students for each subject
    
    **📊 Bar Charts:**
    - **Average Scores**: Shows mean performance for each subject
    
    **📈 Metrics Cards:**
    - **Total Students**: Number of students evaluated
    - **Average Score**: Overall mean performance
    - **Highest/Lowest**: Best and worst performances
    
    ### 🎯 **Step-by-step guide:**
    
    1. **Prepare Answer Key Excel File:**
       - Create an Excel file with subjects as columns
       - Each column should contain the correct answers for that subject
       - Use either letters (a, b, c, d) or numbers (1, 2, 3, 4)
    
    2. **Upload Answer Key:**
       - Click "Browse files" in Step 1
       - Select your Excel answer key file
       - Verify the preview looks correct
    
    3. **Upload OMR Sheets:**
       - Take clear, well-lit photos of OMR sheets
       - Ensure the sheet is flat and all bubbles are visible
       - Upload one or multiple images
    
    4. **Start Evaluation:**
       - Optionally enter a student name
       - Click "Start Evaluation"
       - Review results and interactive charts
       - Download CSV reports as needed
    
    ### 💡 **Tips for better accuracy:**
    - Ensure good lighting when photographing OMR sheets
    - Keep the camera steady and parallel to the sheet
    - Make sure all bubbles are clearly visible
    - Avoid shadows on the sheet
    - Enable debug mode to see detailed processing steps
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <a href='https://github.com/Yaazhini25/omr-evaluation-system' target='_blank'>GitHub Repository</a>
    </div>
    """, 
    unsafe_allow_html=True
)
