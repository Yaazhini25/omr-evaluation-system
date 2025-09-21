# db_setup.py
import sqlite3
import os


DB_FILE = "omr_results.db"


def init_db(subjects=None):
    """
    Initialize the database with dynamic columns based on subjects
    """
    if subjects is None:
        subjects = []
    
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
    print(f"Database initialized with subjects: {subjects}")


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
        return False


def get_all_results():
    """
    Retrieve all results from database
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results';")
        if not c.fetchone():
            conn.close()
            return [], []
        
        # Get all data
        c.execute("SELECT * FROM results ORDER BY Created_At DESC")
        data = c.fetchall()
        
        # Get column names
        col_names = [description[0] for description in c.description]
        
        conn.close()
        return data, col_names
        
    except Exception as e:
        print(f"Error retrieving results: {str(e)}")
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