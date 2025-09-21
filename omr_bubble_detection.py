# omr_bubble_detection.py
import cv2
import numpy as np


def find_bubble_grid(thresh_img, debug=False):
    """
    Find and sort bubble contours in a grid pattern
    """
    # Find all contours
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubble_contours = []
    
    # Filter contours that look like bubbles
    img_area = thresh_img.shape[0] * thresh_img.shape[1]
    min_area = img_area * 0.0001  # Minimum 0.01% of image
    max_area = img_area * 0.01    # Maximum 1% of image
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue
            
        # Check if contour is roughly circular
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
            
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        
        # Filter based on shape properties
        if (circularity > 0.3 and  # Reasonably circular
            0.6 <= aspect_ratio <= 1.4 and  # Roughly square
            w > 10 and h > 10):  # Minimum size
            
            bubble_contours.append({
                'contour': contour,
                'x': x, 'y': y, 'w': w, 'h': h,
                'center_x': x + w//2,
                'center_y': y + h//2,
                'area': area
            })
    
    if debug:
        print(f"Found {len(bubble_contours)} potential bubbles")
    
    # Sort bubbles: first by row (y-coordinate), then by column (x-coordinate)
    bubble_contours.sort(key=lambda b: (b['center_y'], b['center_x']))
    
    return bubble_contours


def group_bubbles_into_questions(bubble_contours, choices_per_question=5):
    """
    Group bubbles into questions based on their positions
    """
    if not bubble_contours:
        return []
    
    questions = []
    current_row_y = bubble_contours[0]['center_y']
    current_question = []
    row_threshold = 30  # Pixels tolerance for same row
    
    for bubble in bubble_contours:
        # If bubble is in roughly the same row
        if abs(bubble['center_y'] - current_row_y) <= row_threshold:
            current_question.append(bubble)
        else:
            # New row - save current question if it has the right number of choices
            if len(current_question) == choices_per_question:
                # Sort by x-coordinate within the question
                current_question.sort(key=lambda b: b['center_x'])
                questions.append(current_question)
            
            # Start new question
            current_question = [bubble]
            current_row_y = bubble['center_y']
    
    # Don't forget the last question
    if len(current_question) == choices_per_question:
        current_question.sort(key=lambda b: b['center_x'])
        questions.append(current_question)
    
    return questions


def extract_bubbles_for_innomatics_sheet(thresh_img, debug=False):
    """
    Specialized extraction for Innomatics OMR sheet format
    5 subjects x 20 questions each = 100 questions total
    Each question has 4 options (A, B, C, D)
    """
    height, width = thresh_img.shape
    
    # Define the approximate layout based on the image structure
    # The OMR sheet has 5 columns (subjects) and questions are arranged vertically
    
    subjects = ['PYTHON', 'DATA ANALYSIS', 'MySQL', 'POWER BI', 'Adv STATS']
    questions_per_subject = 20
    choices_per_question = 4  # A, B, C, D
    
    student_answers = []
    
    # Approximate column boundaries (adjust based on actual sheet dimensions)
    col_width = width // 5
    
    for subject_idx in range(5):  # 5 subjects
        subject_answers = []
        
        # Define column boundaries
        col_start = subject_idx * col_width
        col_end = (subject_idx + 1) * col_width
        
        # Extract the column for this subject
        subject_column = thresh_img[:, col_start:col_end]
        
        # Process questions in this subject (1-20)
        for q in range(questions_per_subject):
            # Calculate approximate row position for this question
            # Questions are numbered 1-20, but arranged in different patterns per subject
            
            if subject_idx == 0:  # PYTHON: 1-20 in order
                question_num = q + 1
            elif subject_idx == 1:  # DATA ANALYSIS: 21-40
                question_num = q + 21
            elif subject_idx == 2:  # MySQL: 41-60  
                question_num = q + 41
            elif subject_idx == 3:  # POWER BI: 61-80
                question_num = q + 61
            else:  # Adv STATS: 81-100
                question_num = q + 81
            
            # Find the actual row for this question number in the image
            row_found = False
            question_row_y = -1
            
            # Look for question number pattern in the image
            # For now, use uniform distribution as fallback
            rows_per_section = height // 25  # Approximate rows per question group
            
            if question_num <= 5:
                question_row_y = (question_num - 1) * rows_per_section
            elif question_num <= 10:
                question_row_y = (question_num - 6) * rows_per_section + height // 4
            elif question_num <= 15:
                question_row_y = (question_num - 11) * rows_per_section + height // 2
            elif question_num <= 20:
                question_row_y = (question_num - 16) * rows_per_section + 3 * height // 4
            
            # Extract the row region for this question
            row_start = max(0, question_row_y - rows_per_section // 2)
            row_end = min(height, question_row_y + rows_per_section // 2)
            
            question_row = subject_column[row_start:row_end, :]
            
            # Find bubbles in this row (A, B, C, D)
            bubble_ratios = []
            bubble_width = question_row.shape[1] // 4
            
            for choice in range(4):  # A, B, C, D
                choice_start = choice * bubble_width
                choice_end = (choice + 1) * bubble_width
                
                bubble_region = question_row[:, choice_start:choice_end]
                
                if bubble_region.size == 0:
                    bubble_ratios.append(0)
                    continue
                
                # Calculate filled ratio
                total_pixels = bubble_region.shape[0] * bubble_region.shape[1]
                filled_pixels = np.count_nonzero(bubble_region)
                filled_ratio = filled_pixels / total_pixels if total_pixels > 0 else 0
                
                bubble_ratios.append(filled_ratio)
            
            # Select the choice with highest fill ratio
            if bubble_ratios and max(bubble_ratios) > 0.05:  # At least 5% filled
                selected_choice = np.argmax(bubble_ratios) + 1  # Convert to 1-based (A=1, B=2, C=3, D=4)
            else:
                selected_choice = 1  # Default to A if nothing clear
            
            subject_answers.append(selected_choice)
            
            if debug and subject_idx == 0 and q < 5:
                print(f"Subject {subject_idx+1}, Q{question_num}: ratios={[f'{r:.3f}' for r in bubble_ratios]}, selected={selected_choice}")
        
        student_answers.extend(subject_answers)
    
    if debug:
        print(f"Total extracted answers: {len(student_answers)}")
        print(f"First 20 answers: {student_answers[:20]}")
    
    return student_answers


def extract_bubbles(thresh_img, num_subjects=5, questions_per_subject=20, choices_per_question=4, debug=False):
    """
    Main bubble extraction function - routes to specialized version for Innomatics sheets
    """
    if num_subjects == 5 and questions_per_subject == 20 and choices_per_question == 4:
        return extract_bubbles_for_innomatics_sheet(thresh_img, debug)
    
    # Fallback to original method for other formats
    return extract_bubbles_generic(thresh_img, num_subjects, questions_per_subject, choices_per_question, debug)


def extract_bubbles_generic(thresh_img, num_subjects=5, questions_per_subject=20, choices_per_question=5, debug=False):
    """
    Detect filled bubbles and return answers as numbers (1-5)
    """
    total_expected_questions = num_subjects * questions_per_subject
    
    # Find all bubble contours
    bubble_contours = find_bubble_grid(thresh_img, debug)
    
    if len(bubble_contours) == 0:
        if debug:
            print("No bubbles detected!")
        return [1] * total_expected_questions  # Default answers
    
    # Group bubbles into questions
    questions = group_bubbles_into_questions(bubble_contours, choices_per_question)
    
    if debug:
        print(f"Grouped into {len(questions)} questions")
        print(f"Expected {total_expected_questions} questions")
    
    student_answers = []
    
    for question_idx, question_bubbles in enumerate(questions):
        if len(question_bubbles) != choices_per_question:
            # Skip malformed questions
            student_answers.append(1)  # Default to option A
            continue
        
        # Calculate filled ratio for each choice
        choice_ratios = []
        for bubble in question_bubbles:
            x, y, w, h = bubble['x'], bubble['y'], bubble['w'], bubble['h']
            
            # Extract bubble region with some padding
            padding = 2
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(thresh_img.shape[1], x + w + padding)
            y2 = min(thresh_img.shape[0], y + h + padding)
            
            bubble_roi = thresh_img[y1:y2, x1:x2]
            
            if bubble_roi.size == 0:
                choice_ratios.append(0)
                continue
            
            # Calculate how much of the bubble is filled
            total_pixels = bubble_roi.shape[0] * bubble_roi.shape[1]
            filled_pixels = np.count_nonzero(bubble_roi)
            filled_ratio = filled_pixels / total_pixels if total_pixels > 0 else 0
            
            choice_ratios.append(filled_ratio)
        
        if not choice_ratios:
            student_answers.append(1)
            continue
        
        # Find the choice with maximum fill ratio
        max_ratio_idx = np.argmax(choice_ratios)
        max_ratio = choice_ratios[max_ratio_idx]
        
        # Only consider it filled if ratio is above threshold
        if max_ratio > 0.1:  # At least 10% filled
            selected_answer = max_ratio_idx + 1  # Convert to 1-based
        else:
            selected_answer = 1  # Default if nothing is clearly marked
        
        student_answers.append(selected_answer)
        
        if debug and question_idx < 5:  # Debug first 5 questions
            print(f"Question {question_idx + 1}: Ratios {[f'{r:.3f}' for r in choice_ratios]}, Selected: {selected_answer}")
    
    # Pad or truncate to expected number of questions
    while len(student_answers) < total_expected_questions:
        student_answers.append(1)  # Default answers for missing questions
    
    if len(student_answers) > total_expected_questions:
        student_answers = student_answers[:total_expected_questions]
    
    if debug:
        print(f"Final answers: {student_answers[:10]}...")  # Show first 10
    
    return student_answers