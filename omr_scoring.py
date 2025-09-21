# omr_scoring.py


def convert_answer_key_letters(answer_key):
    """
    Convert letter answers (a, b, c, d) to numbers (1, 2, 3, 4)
    Handle both strings and numbers
    """
    letter_map = {"a": 1, "b": 2, "c": 3, "d": 4, "A": 1, "B": 2, "C": 3, "D": 4}
    converted = []
    
    for ans in answer_key:
        if isinstance(ans, str):
            ans_clean = ans.strip().lower()
            if ans_clean in letter_map:
                converted.append(letter_map[ans_clean])
            else:
                # Try to convert to int if it's a number string
                try:
                    ans_int = int(ans_clean)
                    if 1 <= ans_int <= 4:
                        converted.append(ans_int)
                    else:
                        converted.append(1)  # Default to 1 if out of range
                except (ValueError, TypeError):
                    converted.append(1)  # Default to 1 if can't convert
        elif isinstance(ans, (int, float)):
            # Ensure it's in valid range
            ans_int = int(ans)
            if 1 <= ans_int <= 4:
                converted.append(ans_int)
            else:
                converted.append(1)  # Default
        else:
            converted.append(1)  # Default for any other type
    
    return converted


def calculate_score(student_answers, answer_key, num_subjects=5, questions_per_subject=20, debug=False):
    """
    Calculate scores for each subject and total score
    """
    # Convert answer key to numbers
    answer_key_numbers = convert_answer_key_letters(answer_key)
    
    total_expected_questions = num_subjects * questions_per_subject
    
    # Ensure both lists have the same length
    if len(student_answers) != total_expected_questions:
        if debug:
            print(f"Warning: Student answers length {len(student_answers)} != expected {total_expected_questions}")
        # Pad or truncate student answers
        while len(student_answers) < total_expected_questions:
            student_answers.append(1)
        student_answers = student_answers[:total_expected_questions]
    
    if len(answer_key_numbers) != total_expected_questions:
        if debug:
            print(f"Warning: Answer key length {len(answer_key_numbers)} != expected {total_expected_questions}")
        # Pad or truncate answer key
        while len(answer_key_numbers) < total_expected_questions:
            answer_key_numbers.append(1)
        answer_key_numbers = answer_key_numbers[:total_expected_questions]
    
    subject_scores = []
    
    if debug:
        print(f"Calculating scores for {num_subjects} subjects, {questions_per_subject} questions each")
        print(f"Student answers sample: {student_answers[:10]}")
        print(f"Answer key sample: {answer_key_numbers[:10]}")
    
    for subject_idx in range(num_subjects):
        start_idx = subject_idx * questions_per_subject
        end_idx = (subject_idx + 1) * questions_per_subject
        
        student_section = student_answers[start_idx:end_idx]
        key_section = answer_key_numbers[start_idx:end_idx]
        
        # Count correct answers
        correct_count = 0
        for student_ans, correct_ans in zip(student_section, key_section):
            if student_ans == correct_ans:
                correct_count += 1
        
        subject_scores.append(correct_count)
        
        if debug:
            print(f"Subject {subject_idx + 1}: {correct_count}/{questions_per_subject} correct")
            if subject_idx == 0:  # Show details for first subject
                print(f"  Student: {student_section}")
                print(f"  Correct: {key_section}")
    
    total_score = sum(subject_scores)
    
    if debug:
        print(f"Final scores: {subject_scores}, Total: {total_score}")
    
    return subject_scores, total_score