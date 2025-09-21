# db_setup.py
import sqlite3
import os
import tempfile


# Use a temporary directory that's writable in deployed environments
if "STREAMLIT_CLOUD" in os.environ or any(key in os.environ for key in ["DYNO", "RAILWAY_", "RENDER"]):
    # Deployed environment - use temp directory
    DB_DIR = tempfile.gettempdir()
    DB_FILE = os.path.join(DB_DIR, "omr_results.db")
else:
    # Local environment
    DB_FILE = "omr_results.db"


def init_db(subjects=None):
    """
    Initialize the database with dynamic columns based on subjects
    """
    if subjects is None:
        subjects = []
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Drop existing table to recreate with new structure
        c.execute("DROP TABLE IF EXISTS results")
        
        # Create columns string for subjects
        if subjects:
            subject_cols = ", ".join([f'"{subject}" INTEGER' for subject in subjects])
            sql = f"""
                CREATE TABLE results (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Student TEXT NOT NULL,
                    {subject_cols},
                    Total INTEGER,
                    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        else:
            # Default table structure
            sql = """
                CREATE TABLE results (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Student TEXT NOT NULL,
                    Subject1 INTEGER,
                    Subject2 INTEGER,
                    Subject3 INTEGER,
                    Subject4 INTEGER,
                    Subject5 INTEGER,
                    Total INTEGER,
                    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        
        c.execute(sql)
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at: {DB_FILE}")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False


def save_results(student_name, subject_scores, total_score, subjects):
    """
    Save evaluation results to database
    """
    if not student_name or not subjects or not subject_scores:
        print("Invalid data provided to save_results")
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Prepare column names and values
        subject_cols = ", ".join([f'"{subject}"' for subject in subjects])
        placeholders = ", ".join(["?"] * (len(subjects) + 2))  # +2 for Student and Total
        
        sql = f"""
            INSERT INTO results (Student, {subject_cols}, Total)
            VALUES ({placeholders})
        """
        
        # Prepare values tuple
        values = [student_name] + list(subject_scores) + [total_score]
        
        c.execute(sql, values)
        conn.commit()
        conn.close()
        
        print(f"Successfully saved results for {student_name}")
        return True
        
    except Exception as e:
        print(f"Error saving results: {str(e)}")
        # Try alternative approach - create in-memory storage
        try:
            if 'results_cache' not in st.session_state:
                st.session_state.results_cache = []
            
            result = {
                'Student': student_name,
                'Total': total_score,
                'timestamp': pd.Timestamp.now()
            }
            for i, subject in enumerate(subjects):
                result[subject] = subject_scores[i]
            
            st.session_state.results_cache.append(result)
            print(f"Saved to session cache for {student_name}")
            return True
        except:
            return False


def get_all_results():
    """
    Retrieve all results from database or session cache
    """
    try:
        # Try database first
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results';")
        if not c.fetchone():
            conn.close()
            # Fallback to session cache
            return get_results_from_cache()
        
        # Get all data
        c.execute("SELECT * FROM results ORDER BY Created_At DESC")
        data = c.fetchall()
        
        # Get column names
        col_names = [description[0] for description in c.description]
        
        conn.close()
        return data, col_names
        
    except Exception as e:
        print(f"Error retrieving results from database: {str(e)}")
        # Fallback to session cache
        return get_results_from_cache()


def get_results_from_cache():
    """
    Get results from session state cache as fallback
    """
    try:
        import streamlit as st
        if 'results_cache' in st.session_state and st.session_state.results_cache:
            cache_data = st.session_state.results_cache
            if cache_data:
                # Convert to format expected by calling code
                df = pd.DataFrame(cache_data)
                data = [tuple(row) for row in df.values]
                col_names = df.columns.tolist()
                return data, col_names
        return [], []
    except Exception as e:
        print(f"Error retrieving from cache: {str(e)}")
        return [], []


def delete_all_results():
    """
    Delete all results from database (for testing purposes)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM results")
        conn.commit()
        conn.close()
        print("All results deleted successfully")
        return True
    except Exception as e:
        print(f"Error deleting results: {str(e)}")
        return False


def get_database_info():
    """
    Get information about the database structure
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results';")
        if not c.fetchone():
            conn.close()
            return {"exists": False}
        
        # Get table info
        c.execute("PRAGMA table_info(results)")
        table_info = c.fetchall()
        
        # Get row count
        c.execute("SELECT COUNT(*) FROM results")
        row_count = c.fetchone()[0]
        
        conn.close()
        
        return {
            "exists": True,
            "columns": table_info,
            "row_count": row_count
        }
        
    except Exception as e:
        print(f"Error getting database info: {str(e)}")
        return {"exists": False, "error": str(e)}


def reset_database():
    """
    Reset the database by deleting the file
    """
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"Database file {DB_FILE} deleted successfully")
            return True
        else:
            print(f"Database file {DB_FILE} does not exist")
            return True
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        return False
