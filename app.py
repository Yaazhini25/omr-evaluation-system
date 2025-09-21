# app.py
import streamlit as st
from omr_preprocessing import preprocess_omr
from omr_bubble_detection import extract_bubbles
from omr_scoring import calculate_score
from db_setup import init_db, save_results, get_all_results
import pandas as pd
import numpy as np


st.set_page_config(page_title="OMR Evaluation System", layout="wide")
st.title("🎯 Automated OMR Evaluation System")

# Initialize session state
if 'answer_key_loaded' not in st.session_state:
    st.session_state.answer_key_loaded = False
if 'answer_key' not in st.session_state:
    st.session_state.answer_key = None
if 'subject_names' not in st.session_state:
    st.session_state.subject_names = []

# Sidebar for configuration
st.sidebar.header("Configuration")
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Step 1: Upload Answer Key")
    
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
            st.write("**Answer Key Preview:**")
            st.dataframe(df_key.head())
            
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
            
            st.success(f"✅ Answer key loaded successfully!")
            st.info(f"**Subjects:** {', '.join(subject_names)}")
            st.info(f"**Questions per subject:** {questions_per_subject}")
            st.info(f"**Total questions:** {len(answer_key_flat)}")
            
            # Initialize database
            init_db(subject_names)
            
            if debug_mode:
                st.write("**Debug - Answer Key Sample:**", answer_key_flat[:10])
                
        except Exception as e:
            st.error(f"❌ Error loading answer key: {str(e)}")
            st.session_state.answer_key_loaded = False

with col2:
    st.header("📄 Step 2: Upload OMR Sheets")
    
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
st.header("🔍 Step 3: Evaluate OMR Sheets")

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
                    
                    # Show individual result
                    st.subheader(f"Results for {student_name}")
                    result_df = pd.DataFrame([result_dict])
                    st.dataframe(result_df, use_container_width=True)
                    
                    if debug_mode:
                        st.write("**Debug Info:**")
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
            st.header("📊 Summary Results")
            
            summary_df = pd.DataFrame(all_results)
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
            
            # Show statistics
            st.header("📈 Statistics")
            
            stats_col1, stats_col2 = st.columns([1, 1])
            
            with stats_col1:
                st.subheader("Subject-wise Average Scores")
                subject_averages = {}
                for subject in st.session_state.subject_names:
                    if subject in summary_df.columns:
                        avg_score = summary_df[subject].mean()
                        subject_averages[subject] = avg_score
                        st.metric(subject, f"{avg_score:.1f}")
            
            with stats_col2:
                st.subheader("Overall Statistics")
                if 'Total' in summary_df.columns:
                    total_avg = summary_df['Total'].mean()
                    total_max = summary_df['Total'].max()
                    total_min = summary_df['Total'].min()
                    
                    st.metric("Average Total Score", f"{total_avg:.1f}")
                    st.metric("Highest Score", f"{total_max}")
                    st.metric("Lowest Score", f"{total_min}")
                
                st.metric("Total Students Evaluated", len(summary_df))

# Show all previous results
st.header("📋 Previous Results")
try:
    all_data, col_names = get_all_results()
    if all_data and len(all_data) > 0:
        df_all = pd.DataFrame(all_data, columns=col_names)
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
        st.info("No previous results found.")
except Exception as e:
    st.error(f"Error loading previous results: {str(e)}")

# Add some helpful information
with st.expander("ℹ️ How to use this system"):
    st.write("""
    **Step-by-step guide:**
    
    1. **Prepare Answer Key Excel File:**
       - Create an Excel file with subjects as columns
       - Each column should contain the correct answers for that subject
       - Use either letters (A, B, C, D, E) or numbers (1, 2, 3, 4, 5)
    
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
       - Review results and download as needed
    
    **Tips for better accuracy:**
    - Ensure good lighting when photographing OMR sheets
    - Keep the camera steady and parallel to the sheet
    - Make sure all bubbles are clearly visible
    - Avoid shadows on the sheet
    """)