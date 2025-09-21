# 🎯 Automated OMR Evaluation & Scoring System

An automated OMR (Optical Mark Recognition) evaluation system built for Innomatics Research Labs to process placement readiness assessments efficiently.

## 📋 Problem Statement

At Innomatics Research Labs, we conduct placement readiness assessments across roles like Data Analytics and AI/ML for Data Science with Generative AI courses. Each exam uses standardized OMR sheets with 100 questions distributed as 20 per subject across 5 subjects.

The manual evaluation process was:
- ⏰ Time-consuming (delays in releasing results)
- ❌ Error-prone (human miscounts)
- 💰 Resource-intensive (requires multiple evaluators)

## 🚀 Solution

This automated system provides:
- 📱 Mobile phone camera capture support
- 🔄 Automatic image preprocessing and perspective correction
- 🎯 Accurate bubble detection using Computer Vision
- 📊 Subject-wise scoring and total score calculation
- 🌐 Web-based interface for easy evaluation
- 📈 Real-time results and statistics
- 💾 Secure database storage with audit trail

## 🛠️ Tech Stack

### Core OMR Processing
- **Python** - Primary programming language
- **OpenCV** - Image preprocessing, bubble detection, perspective correction
- **NumPy** - Image array manipulation and calculations
- **Pandas** - Data processing and Excel handling
- **SQLite** - Database for storing results

### Web Application
- **Streamlit** - Frontend web interface
- **Pillow** - Image manipulation and format conversion

## 📦 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Yaazhini25/omr-evaluation-system.git
cd omr-evaluation-system
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
streamlit run app.py
```

## 🎮 Usage

### Step 1: Prepare Answer Key
- Create an Excel file with subjects as columns (Python, EDA, SQL, POWER BI, Statistics)
- Each column should contain 20 correct answers in format "1 - a", "2 - b", etc.
- Use letters a, b, c, d for the 4 answer choices

### Step 2: Upload Answer Key
- Click "Browse files" and select your Excel answer key
- Verify the preview shows correct subjects and answers

### Step 3: Upload OMR Sheets
- Take clear, well-lit photos of completed OMR sheets
- Ensure sheets are flat with all bubbles clearly visible
- Upload one or multiple images (PNG, JPG, JPEG)

### Step 4: Evaluate
- Optionally enter student name
- Click "Start Evaluation" 
- Review results and download CSV reports

## 📊 Features

- ✅ **<0.5% Error Tolerance** - Meets Innomatics quality standards
- ⚡ **Minutes vs Days** - Reduces evaluation time from days to minutes
- 🔍 **Debug Mode** - Shows processing steps for troubleshooting
- 📈 **Real-time Statistics** - Subject-wise averages and performance metrics
- 💾 **Data Persistence** - All results stored in SQLite database
- 📱 **Mobile Compatible** - Works with smartphone camera captures
- 🌐 **Web Interface** - Easy-to-use browser-based evaluation

## 🗂️ Project Structure

```
omr-evaluation-system/
├── app.py                      # Main Streamlit application
├── omr_preprocessing.py        # Image preprocessing functions
├── omr_bubble_detection.py     # Bubble detection algorithms
├── omr_scoring.py             # Scoring and answer key processing
├── omr_results.db             # Backend DB to view the results
├── ans_key.py                 # Load the answer key excel file
├── db_setup.py                # Database operations
├── db_drop.py                 # Drop old database
├── db_checkup.py              # To verify database on the backend 
├── requirements.txt           # Python dependencies
├── README.md
├── ans key
    ├── Key (Set A and B)                  # Answer key to verify
└── input-images/              # Sample OMR sheets and answer keys
    ├── Img1.jpeg
    └── Img2.jpeg
    ├── Img3.jpeg
    └── Img4.jpeg
    ├── Img5.jpeg
    └── Img6.jpeg
    ├── Img7.jpeg
    └── Img8.jpeg
    ├── Img9.jpeg
    └── Img10.jpeg
    ├── Img11.jpeg
    └── Img12.jpeg
    ├── Img13.jpeg
    └── Img14.jpeg
    ├── Img15.jpeg
    └── Img16.jpeg
```

## 🔧 Configuration

The system is pre-configured for Innomatics OMR sheet format:
- **5 Subjects**: Python, EDA, SQL, Power BI, Statistics
- **20 Questions per Subject** (Total: 100 questions)
- **4 Answer Choices**: A, B, C, D per question

To modify for different formats, update the parameters in `extract_bubbles()` function.

### Main Interface
- Upload answer key and OMR sheets
- Real-time processing with progress indicators
- Individual sheet results display

### Results Dashboard  
- Subject-wise score breakdown
- Overall statistics and analytics
- CSV export functionality

## 🐛 Troubleshooting

### Common Issues:

1. **All subjects showing 0 scores:**
   - Ensure OMR sheet image is clear and well-lit
   - Check that bubbles are properly filled (dark marks)
   - Verify answer key format matches expected structure

2. **All subjects showing maximum scores:**
   - Enable debug mode to see detection details
   - Check if image preprocessing is working correctly
   - Verify answer key mapping is correct

3. **"Too many values to unpack" error:**
   - This has been fixed in the latest version
   - Ensure you're using the updated code files

### Tips for Better Accuracy:
- 📷 Use good lighting when photographing OMR sheets
- 📐 Keep camera parallel to the sheet surface
- 🎯 Ensure all bubbles are clearly visible
- 🚫 Avoid shadows on the answer sheet


## 👥 Author

- **Yaazhini S** - *Initial work* - https://github.com/Yaazhini25/omr-evaluation-system

⭐ **Star this repository if it helps you!** ⭐
