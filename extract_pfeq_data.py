#!/usr/bin/env python3
"""
PFEQ PDF Data Extraction Script
Extracts curriculum data from PFEQ PDF documents and generates JavaScript code
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
import pypdf

# Subject name mappings from filenames
SUBJECT_MAPPINGS = {
    'histoire': 'History and Citizenship Education',
    'history': 'History and Citizenship Education',
    'geographie': 'Geography',
    'geography': 'Geography',
    'science': 'Science and Technology',
    'mathematique': 'Mathematics',
    'mathematics': 'Mathematics',
    'math': 'Mathematics',
    'english': 'English Language Arts',
    'langue': 'English Language Arts',
}

# Grade level patterns - now includes preschool and elementary
GRADE_PATTERNS = [
    # Preschool
    (r'preschool|prescolaire', 'Preschool'),
    (r'pre-school|pre-scolaire', 'Preschool'),
    
    # Elementary
    (r'elementary|primaire', 'Elementary'),
    (r'grade\s*([1-6])', 'Elementary {}'),
    (r'cycle\s*([1-3])\s*elementary', 'Elementary {}'),
    
    # Secondary
    (r'secondary\s*([1-5])', 'Secondary {}'),
    (r'secondaire\s*([1-5])', 'Secondary {}'),
    (r'cycle1|cycle\s*1|premier\s*cycle|premier-cycle', 'Secondary 1'),
    (r'cycle2|cycle\s*2|deuxieme\s*cycle|deuxieme-cycle', 'Secondary 4'),
]

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF file using pdfplumber (better for complex layouts)"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting from {pdf_path.name} with pdfplumber: {e}")
        # Fallback to pypdf
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e2:
            print(f"Error extracting from {pdf_path.name} with pypdf: {e2}")
            return ""

def identify_subject_grade(filename: str, text: str) -> Tuple[Optional[str], List[str]]:
    """Identify subject and grade from filename and/or text"""
    filename_lower = filename.lower()
    text_lower = text[:5000].lower() if len(text) > 5000 else text.lower()
    
    # Identify subject from filename patterns
    subject = None
    
    # More specific filename patterns first
    if 'histoire' in filename_lower or 'history' in filename_lower:
        if 'quebec-canada' in filename_lower or '20e-siecle' in filename_lower or '20th' in filename_lower:
            subject = 'History and Citizenship Education'
        elif 'education-citoyennete' in filename_lower or 'citizenship' in filename_lower:
            subject = 'History and Citizenship Education'
        else:
            subject = 'History and Citizenship Education'
    elif 'geographie' in filename_lower or 'geography' in filename_lower:
        if 'culturelle' in filename_lower or 'cultural' in filename_lower:
            subject = 'Geography'
        else:
            subject = 'Geography'
    elif 'science' in filename_lower and 'technologie' in filename_lower:
        subject = 'Science and Technology'
    elif 'mathematique' in filename_lower or 'mathematics' in filename_lower or 'math' in filename_lower:
        subject = 'Mathematics'
    elif 'english' in filename_lower or 'langue' in filename_lower:
        subject = 'English Language Arts'
    
    # Fallback to general mappings
    if not subject:
        for key, value in SUBJECT_MAPPINGS.items():
            if key in filename_lower:
                subject = value
                break
    
    # If still not found, check text
    if not subject:
        for key, value in SUBJECT_MAPPINGS.items():
            if key in text_lower[:2000]:
                subject = value
                break
    
    # Identify grade - IMPROVED: More specific grade detection
    grade = None
    grades_list = []
    
    # IMPROVED: Check for specific cycle patterns in filename (more comprehensive)
    if '1ercycle' in filename_lower or '1er-cycle' in filename_lower or 'premier-cycle' in filename_lower or 'cycle1' in filename_lower:
        # First cycle = Secondary 1 and 2
        grades_list = ['Secondary 1', 'Secondary 2']
    elif '2ecycle' in filename_lower or '2e-cycle' in filename_lower or 'deuxieme-cycle' in filename_lower or 'cycle2' in filename_lower:
        # Second cycle = Secondary 4 and 5
        grades_list = ['Secondary 4', 'Secondary 5']
    elif '3ecycle' in filename_lower or '3e-cycle' in filename_lower or 'troisieme-cycle' in filename_lower:
        # Third cycle = Elementary 5 and 6
        grades_list = ['Elementary 5', 'Elementary 6']
    elif '2ecycle' in filename_lower or '2e-cycle' in filename_lower:
        # Second cycle elementary = Elementary 3 and 4
        grades_list = ['Elementary 3', 'Elementary 4']
    elif '1ercycle' in filename_lower or '1er-cycle' in filename_lower:
        # First cycle elementary = Elementary 1 and 2
        grades_list = ['Elementary 1', 'Elementary 2']
    else:
        # Check for specific numbered grades in filename
        for pattern, template in GRADE_PATTERNS:
            match = re.search(pattern, filename_lower, re.IGNORECASE)
            if match:
                if 'cycle' in pattern.lower() and '{}' not in template:
                    grade = template
                elif '{}' in template:
                    grade = template.format(match.group(1))
                else:
                    grade = template
                if grade:
                    grades_list.append(grade)
                break
        
        # If no grade found in filename, check text more thoroughly
        if not grades_list:
            # Look for specific grade mentions in text (first 10000 chars)
            text_sample = text_lower[:10000]
            
            # Check for specific secondary grades
            for i in range(1, 6):
                patterns = [
                    f'secondary {i}',
                    f'secondaire {i}',
                    f'sec {i}',
                    f'grade {i}.*secondary',
                    f'niveau {i}.*secondaire'
                ]
                for pattern in patterns:
                    if re.search(pattern, text_sample, re.IGNORECASE):
                        grades_list.append(f'Secondary {i}')
                        break
            
            # Check for specific elementary grades
            if not grades_list:
                for i in range(1, 7):
                    patterns = [
                        f'elementary {i}',
                        f'primaire {i}',
                        f'grade {i}.*elementary',
                        f'niveau {i}.*primaire'
                    ]
                    for pattern in patterns:
                        if re.search(pattern, text_sample, re.IGNORECASE):
                            grades_list.append(f'Elementary {i}')
                            break
            
            # Check for cycle mentions in text
            if not grades_list:
                if re.search(r'first cycle|premier cycle|cycle 1|1er cycle', text_sample, re.IGNORECASE):
                    if 'secondary' in text_sample or 'secondaire' in text_sample:
                        grades_list = ['Secondary 1', 'Secondary 2']
                    elif 'elementary' in text_sample or 'primaire' in text_sample:
                        grades_list = ['Elementary 1', 'Elementary 2']
                elif re.search(r'second cycle|deuxieme cycle|cycle 2|2e cycle', text_sample, re.IGNORECASE):
                    if 'secondary' in text_sample or 'secondaire' in text_sample:
                        grades_list = ['Secondary 4', 'Secondary 5']
                    elif 'elementary' in text_sample or 'primaire' in text_sample:
                        grades_list = ['Elementary 3', 'Elementary 4']
                elif re.search(r'third cycle|troisieme cycle|cycle 3|3e cycle', text_sample, re.IGNORECASE):
                    grades_list = ['Elementary 5', 'Elementary 6']
    
    # Fallback: Check filename for general level indicators (only if no specific grades found)
    if not grades_list and subject:
        if 'preschool' in filename_lower or 'prescolaire' in filename_lower:
            grades_list.append('Preschool')
        elif 'elementary' in filename_lower or 'primaire' in filename_lower:
            # Don't default to generic "Elementary" - try to find specific grades
            for i in range(1, 7):
                if f'grade {i}' in filename_lower or f'niveau {i}' in filename_lower:
                    grades_list.append(f'Elementary {i}')
        elif 'secondaire' in filename_lower or 'secondary' in filename_lower:
            # Don't default to all secondary grades - only if it's a main curriculum doc
            # Check if it's a main program document (not a supplementary doc)
            is_main_doc = any(kw in filename_lower for kw in ['programme', 'program', 'curriculum', 'pfeq'])
            if is_main_doc and 'progression' not in filename_lower and 'cadre' not in filename_lower:
                # Only for main curriculum documents, check text for all grade mentions
                text_sample = text_lower[:15000]
                found_grades = []
                for i in range(1, 6):
                    if re.search(rf'secondary {i}|secondaire {i}|sec {i}', text_sample, re.IGNORECASE):
                        found_grades.append(f'Secondary {i}')
                if found_grades:
                    grades_list = found_grades
    
    # Remove duplicates and sort
    grades_list = sorted(list(set(grades_list)))
    
    return subject, grades_list

def extract_competencies(text: str) -> List[Dict]:
    """Extract competencies from text"""
    competencies = []
    
    # Pattern for competency IDs (e.g., HCE-4-1, GEO-2-1, ST-1-1)
    competency_id_pattern = r'([A-Z]{2,4})-(\d+)-(\d+)'
    
    lines = text.split('\n')
    current_competency = None
    collecting_objectives = False
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # Check for competency ID
        id_match = re.search(competency_id_pattern, line_clean)
        if id_match:
            if current_competency and current_competency.get('name'):
                competencies.append(current_competency)
            
            # Look for competency name in current and next few lines
            name = ""
            # Check current line
            if len(line_clean) > 20 and not re.match(r'^[A-Z]+-\d+-\d+$', line_clean):
                # Might be ID and name on same line
                parts = re.split(competency_id_pattern, line_clean, maxsplit=1)
                if len(parts) > 3:
                    potential_name = parts[-1].strip()
                    if len(potential_name) > 10:
                        name = potential_name
            
            # Check next few lines for name
            if not name:
                for j in range(i+1, min(i+6, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and len(next_line) > 15 and len(next_line) < 200:
                        # Not just an ID, not a bullet point, reasonable length
                        if not re.match(r'^[-•\d]', next_line) and not re.search(competency_id_pattern, next_line):
                            name = next_line
                            break
            
            current_competency = {
                'id': id_match.group(0),
                'name': name or f"Competency {id_match.group(3)}",
                'learningObjectives': []
            }
            collecting_objectives = False
            continue
        
        # If we have a competency, look for learning objectives
        if current_competency:
            # Look for section headers that indicate objectives
            if re.search(r'learning\s+objectives?|objectifs?\s+d\'apprentissage|objectifs?\s+dapprentissage', line_clean, re.IGNORECASE):
                collecting_objectives = True
                continue
            
            # Collect objectives (usually bullet points or numbered)
            if collecting_objectives or i < 20:  # First 20 lines after competency likely contain objectives
                obj_match = re.match(r'^[-•\d]+[\.\)]\s*(.+)$', line_clean)
                if obj_match:
                    obj_text = obj_match.group(1).strip()
                    if len(obj_text) > 15 and len(obj_text) < 300:  # Reasonable length
                        if obj_text not in current_competency['learningObjectives']:
                            current_competency['learningObjectives'].append(obj_text)
    
    if current_competency and current_competency.get('name'):
        competencies.append(current_competency)
    
    return competencies

def extract_cross_curricular_competencies(text: str, subject: str, grade: str, topic: str = None) -> List[str]:
    """Return relevant cross-curricular competencies based on subject type"""
    # Standard 9 cross-curricular competencies in Quebec PFEQ
    all_competencies = [
        # Intellectual
        'Exploiter l\'information',
        'Résoudre des problèmes',
        'Exercer son jugement critique',
        'Mettre en œuvre sa pensée créatrice',
        # Methodological
        'Se donner des méthodes de travail efficaces',
        'Exploiter les technologies de l\'information et de la communication',
        # Personal/Social
        'Structurer son identité',
        'Coopérer',
        # Communication
        'Communiquer de façon appropriée'
    ]
    
    # Subject-specific relevance - all subjects get these core competencies
    # Additional competencies based on subject type
    if 'History' in subject or 'Citizenship' in subject:
        return [
            'Exploiter l\'information',
            'Exercer son jugement critique',
            'Communiquer de façon appropriée',
            'Se donner des méthodes de travail efficaces',
            'Coopérer'
        ]
    elif 'Geography' in subject:
        return [
            'Exploiter l\'information',
            'Exploiter les technologies de l\'information et de la communication',
            'Exercer son jugement critique',
            'Communiquer de façon appropriée',
            'Se donner des méthodes de travail efficaces'
        ]
    elif 'Science' in subject or 'Technology' in subject:
        return [
            'Résoudre des problèmes',
            'Exploiter l\'information',
            'Exploiter les technologies de l\'information et de la communication',
            'Mettre en œuvre sa pensée créatrice',
            'Se donner des méthodes de travail efficaces',
            'Communiquer de façon appropriée'
        ]
    elif 'Mathematics' in subject or 'Math' in subject:
        return [
            'Résoudre des problèmes',
            'Exercer son jugement critique',
            'Mettre en œuvre sa pensée créatrice',
            'Se donner des méthodes de travail efficaces',
            'Communiquer de façon appropriée'
        ]
    elif 'English' in subject or 'Language' in subject:
        return [
            'Communiquer de façon appropriée',
            'Mettre en œuvre sa pensée créatrice',
            'Exercer son jugement critique',
            'Exploiter l\'information',
            'Coopérer'
        ]
    else:
        # Default: core competencies for all subjects
        return [
            'Communiquer de façon appropriée',
            'Se donner des méthodes de travail efficaces',
            'Exploiter l\'information',
            'Coopérer'
        ]

def extract_broad_areas_of_learning(text: str, subject: str, grade: str, topic: str = None) -> List[str]:
    """Return relevant broad areas of learning based on subject type"""
    # Standard 5 broad areas of learning in Quebec PFEQ
    if 'History' in subject or 'Citizenship' in subject:
        return [
            'Vivre-ensemble et citoyenneté',
            'Médias'
        ]
    elif 'Geography' in subject:
        return [
            'Environnement et consommation',
            'Vivre-ensemble et citoyenneté'
        ]
    elif 'Science' in subject or 'Technology' in subject:
        return [
            'Environnement et consommation',
            'Santé et bien-être',
            'Médias'
        ]
    elif 'Mathematics' in subject or 'Math' in subject:
        return [
            'Orientation et entrepreneuriat',
            'Médias'
        ]
    elif 'English' in subject or 'Language' in subject:
        return [
            'Médias',
            'Vivre-ensemble et citoyenneté'
        ]
    else:
        # Default: most universal
        return ['Vivre-ensemble et citoyenneté']

def extract_subject_themes(text: str, subject: str, grade: str) -> List[str]:
    """Return subject-specific broad themes for the grade level"""
    # Subject-specific theme patterns based on Quebec PFEQ
    theme_patterns = {
        'History and Citizenship Education': {
            'Secondary 1': ['First Occupants', 'New France', 'Colonization'],
            'Secondary 2': ['British Rule', 'Conquest', 'New France'],
            'Secondary 3': ['Contemporary Quebec', 'Quebec Modernization', 'Quebec Identity'],
            'Secondary 4': ['Civil Rights', 'Rights and Freedoms', '20th Century'],
            'Secondary 5': ['Contemporary Issues', '20th Century', 'Modern Quebec']
        },
        'Geography': {
            'Secondary 1': ['Territory', 'Population', 'Settlement'],
            'Secondary 2': ['Resources', 'Development', 'Territory'],
            'Secondary 3': ['Territory', 'Resources', 'Development'],
            'Secondary 4': ['Territory', 'Resources', 'Development'],
            'Secondary 5': ['Territory', 'Resources', 'Development']
        },
        'Science and Technology': {
            'Secondary 1': ['Material World', 'Living World', 'Earth and Space'],
            'Secondary 2': ['Material World', 'Living World', 'Earth and Space'],
            'Secondary 3': ['Material World', 'Living World', 'Earth and Space'],
            'Secondary 4': ['Material World', 'Living World', 'Earth and Space'],
            'Secondary 5': ['Material World', 'Living World', 'Earth and Space']
        },
        'Mathematics': {
            'Secondary 1': ['Number Sense', 'Algebra', 'Geometry'],
            'Secondary 2': ['Number Sense', 'Algebra', 'Geometry'],
            'Secondary 3': ['Algebra', 'Geometry', 'Statistics'],
            'Secondary 4': ['Algebra', 'Geometry', 'Statistics'],
            'Secondary 5': ['Algebra', 'Geometry', 'Statistics']
        }
    }
    
    # Get grade-specific themes for subject
    if subject in theme_patterns:
        if grade in theme_patterns[subject]:
            return theme_patterns[subject][grade]
        else:
            # Fallback to any grade themes for this subject
            all_themes = set()
            for grade_themes in theme_patterns[subject].values():
                all_themes.update(grade_themes)
            return list(all_themes)
    
    # No themes defined for this subject
    return []

def extract_history_topics(text: str, grade: str = None, subject: str = None) -> List[Dict]:
    """Extract History topics based on PDF structure - specialized for History subjects"""
    topics = []
    
    if not text or not isinstance(text, str):
        return topics
    
    # Extract grade number if present
    grade_num = None
    if grade:
        if 'secondary' in grade.lower():
            match = re.search(r'secondary\s*(\d+)', grade.lower())
            if match:
                grade_num = int(match.group(1))
    
    lines = text.split('\n')
    
    # Known History topics by grade (fallback if extraction fails)
    known_topics = {
        1: [
            'Sedentarization',
            'The Emergence of Civilisations in Mesopotamia',
            'Athens: a First Experiment in Democracy',
            'Romanisation',
            'The Christianisation of the West in the Middle Ages',
            'The Growth of Cities and Trade'
        ],
        2: [
            'Renaissance: a New Vision of Man',
            'European Expansion Around the World',
            'The American and French Revolutions',
            'Industrialization: an Economic and Social Revolution',
            'The Expansion of the Industrial World',
            'Recognition of Civil Rights and Freedoms'
        ],
        3: [
            'Origins to 1608 The experience of the Indigenous peoples and the colonization attempts',
            '1608-1760 The evolution of colonial society under French rule',
            '1760-1791 The Conquest and the change of empire',
            '1791-1840 The demands and struggles of nationhood'
        ],
        4: [
            '1840-1896 The formation of the Canadian federal system',
            '1896-1945 Nationalisms and the autonomy of Canada',
            '1945-1980 The modernization of Québec and the Quiet Revolution',
            'From 1980 to our times Societal choices in contemporary Québec'
        ]
    }
    
    # Use known topics directly for grades 1-4 (we have exact topics from user)
    extracted_topics = []
    if grade_num in known_topics:
        extracted_topics = known_topics[grade_num]
    
    # Convert extracted topics to topic dictionaries
    seen_names = set()
    for topic_name in extracted_topics:
        # Normalize for duplicate checking
        topic_normalized = re.sub(r'[^\w\s]', '', topic_name.lower())
        if topic_normalized not in seen_names:
            seen_names.add(topic_normalized)
            topics.append({
                'name': topic_name,
                'concepts': [],
                'learningObjectives': [],
                'progression': {'buildsOn': [], 'preparesFor': []}
            })
    
    return topics

def extract_topics(text: str, grade: str = None, subject: str = None) -> List[Dict]:
    """Extract ONLY big unit topics - very strict filtering to avoid clutter"""
    # Use specialized History extraction for History subjects
    if subject and ('History' in subject or 'Citizenship' in subject):
        return extract_history_topics(text, grade=grade, subject=subject)
    
    topics = []
    
    if not text or not isinstance(text, str):
        return topics
    
    # STRICT Patterns to EXCLUDE - filter out everything that's NOT a big unit topic
    exclude_patterns = [
        # COMPETENCY EXCLUSIONS - competencies are evaluation criteria, NOT topics
        r'^COMPETENCY\s*\d+',  # Lines starting with "COMPETENCY 1", "COMPETENCY 2", etc.
        r'^Competency\s*\d+',  # Lines starting with "Competency 1", "Competency 2", etc.
        r'^COMPETENCE\s*\d+',  # French: "COMPETENCE 1"
        r'^Compétence\s*\d+',  # French: "Compétence 1"
        r'^.*COMPETENCY\s*\d+',  # Lines containing "COMPETENCY 1" anywhere
        r'^Understands\s+the',  # Competency action verbs: "Understands the..."
        r'^Interprets\s+',  # "Interprets..."
        r'^Constructs\s+',  # "Constructs..."
        r'^.*Understands\s+the\s+organization',  # "Understands the organization of..."
        r'^.*Interprets\s+a\s+territorial',  # "Interprets a territorial issue"
        r'^.*Constructs\s+.*consciousness',  # "Constructs his/her consciousness"
        r'^.*development\s+of\s+.*competency',  # "development of competency"
        r'^.*competency\s+development',  # "competency development"
        
        # Sub-items (a., b., c., etc.) - these are NOT unit topics
        r'^[a-z][\.\)]\s+',  # Lines starting with lowercase letter + period/paren
        r'^[a-z]\)\s+',  # Lines starting with lowercase letter + paren
        r'^[ivx]+[\.\)]\s+',  # Roman numerals (sub-sections)
        r'^\d+[\.\)]\s+[a-z]',  # Numbered sub-items starting with lowercase
        
        # Sentence fragments and descriptions
        r'^[a-z]',  # Lines starting with lowercase (sentence fragments)
        r'\.$',  # Lines ending with period (likely sentences, not titles)
        r'^[^A-Z]',  # Lines not starting with capital letter (fragments)
        r'^[A-Z][a-z]+\s+(is|are|was|were|has|have|had|does|do|did|will|would|can|could|should|may|might)\s+',  # Sentences
        
        # Generic headers and instructional content
        r'^(THE|LE|LA|LES)\s+(RESEARCH|PROCESS|METHOD|STEPS|QUESTIONS|PROBLEM|INFORMATION|DATA|RESULTS|APPROACH|STRATEGY|PLAN|REVIEW|COMMUNICATE|ORGANIZE|GATHER|FORMULATE|BECOME|AWARE)',
        r'^(SECONDARY|ELEMENTARY|PRESCHOOL|SCHOOL)\s+(EDUCATION|PROGRAM|CYCLE)',
        r'^(CYCLE|CYCLE\s+ONE|CYCLE\s+TWO|CYCLE\s+THREE|PREMIER|DEUXIEME)',
        r'^(LEGEND|TABLE|FIGURE|APPENDIX|BIBLIOGRAPHY|REFERENCES|INDEX|GLOSSARY)',
        r'^(SPECIFIC|COMMON|GENERAL)\s+(CONCEPTS|KNOWLEDGE|COMPETENCIES)',
        r'^(SOCIAL|PERSONAL|INTELLECTUAL|METHODOLOGICAL)\s+(SCIENCES|DEVELOPMENT|COMPETENCIES)',
        r'^(VISUAL|ARTS|MATHEMATICS|SCIENCE|TECHNOLOGY|DRAMA|MUSIC|DANCE)',
        r'^(ENVIRONMENTAL|AWARENESS|CONSUMER|RIGHTS|RESPONSIBILITIES)',
        r'^(FORMULATE|ORGANIZE|GATHER|PROCESS|COMMUNICATE|REVIEW)',
        r'^(OBJECT|SITUATION|INQUIRY|INTERPRETATION|CONSCIOUSNESS)',
        r'^(HISTORICAL|KNOWLEDGE|PHENOMENA|SOCIAL|PHENOMENON)',
        r'^[A-Z\s]{20,}$',  # All-caps long lines (headers)
        r'^\d+[\.\)]\s*$',  # Just numbers
        r'^(DIFFERENTIATED|DIFFERENTIATION|ADAPTATION|MODIFICATION)',  # Instructional strategies
        r'^(ELEMENTS|FOR|WHAT|THAT|MEANS|SOME|SUGGESTIONS)',  # Generic headers
        r'^(IMPLEMENTING|THE|OF|EXPECTATIONS|ASSOCIATED|WITH)',  # Generic headers
        r'^(QEP|REQUIREMENTS|COMPETENCY|LEVELS)',  # Program structure
        r'^(SECONDARY|SCHOOL|EDUCATION|PROGRAMME|BASE|ENRICHI)',  # Program names
        r'^(ACTING|TO|FOSTER|THE|EDUCATIONAL|SUCCESS)',  # Generic phrases
        r'^(ADAPTATION|AND|THE|MODIFICATION|OF)',  # Instructional terms
        r'^(OF|COMPETENCY|LEVELS|SECONDARY|SCHOOL)',  # Generic structure
        r'^[A-Z]{2,}\s+[A-Z]{2,}\s+[A-Z]{2,}',  # Multiple all-caps words (headers)
        
        # Language/grammar patterns (not topics)
        r'^(Languages|Langues|Français|French|English)',
        r'français|langue seconde|immersion',
        
        # Fragments and incomplete phrases
        r'^[A-Z][a-z]+\s+(that|which|who|where|when|how|what)\s+',  # Relative clauses
        r'^(When|Where|How|What|Why|Which|Who)\s+',  # Questions
        r'^(The|A|An)\s+[a-z]+\s+(of|in|on|at|for|with|from|to)\s+',  # Prepositional phrases
    ]
    
    # Main unit topic patterns - only these indicate actual big unit topics
    main_unit_patterns = [
        # History - main periods/themes
        r'^(New France|Nouvelle-France)',
        r'^(British Rule|Régime britannique)',
        r'^(First Occupants|Premiers occupants)',
        r'^(Contemporary Quebec|Québec contemporain)',
        r'^(Quebec Modernization|Modernisation du Québec)',
        r'^(Quebec Identity|Identité québécoise)',
        r'^(Social Change|Changement social)',
        r'^(Civil Rights|Droits civils)',
        r'^(Rights and Freedoms|Droits et libertés)',
        r'^(World War|Guerre mondiale)',
        r'^(First World War|Première Guerre mondiale)',
        r'^(Second World War|Deuxième Guerre mondiale)',
        r'^(Conquest|Conquête)',
        r'^(Colonization|Colonisation)',
        r'^(Indigenous Peoples|Peuples autochtones)',
        r'^(20th Century|20e siècle)',
        # Geography - actual unit topics from PFEQ
        r'^(Urban Territory|Territoire urbain)',
        r'^(Protected Territory|Territoire protégé)',
        r'^(Regional Territory|Territoire régional)',
        r'^(Native Territory|Territoire autochtone)',
        r'^(Agricultural Territory|Territoire agricole)',
        r'^(Metropolis|Métropole)',
        r'^(Natural Park|Parc naturel)',
        r'^(Heritage|Patrimoine)',
        r'^(Natural Hazard|Aléa naturel)',
        r'^(Tourism|Tourisme)',
        r'^(Energy Dependence|Dépendance énergétique)',
        r'^(Industrialization|Industrialisation)',
        r'^(Exploitation of Forests|Exploitation des forêts)',
        r'^(Native People|Peuples autochtones)',
        r'^(Environment at Risk|Environnement en péril)',
        r'^(National Agricultural Space|Espace agricole national)',
        r'^(Territory|Territoire)',
        r'^(Population|Settlement|Établissement)',
        r'^(Resources|Ressources)',
        r'^(Development|Développement)',
        # Science
        r'^(Material World|Monde matériel)',
        r'^(Living World|Monde vivant)',
        r'^(Earth and Space|Terre et espace)',
        r'^(Matter|Matière)',
        r'^(Energy|Énergie)',
        # Math
        r'^(Number Sense|Sens du nombre)',
        r'^(Algebra|Algèbre)',
        r'^(Geometry|Géométrie)',
        r'^(Statistics|Statistiques)',
    ]
    
    lines = text.split('\n')
    seen_topics = set()
    
    # STRICT: Only extract lines that look like main unit titles
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Must be reasonable length (unit titles are typically 2-8 words, 10-80 chars)
        if not line_stripped or len(line_stripped) < 10 or len(line_stripped) > 80:
            continue
        
        # Must start with capital letter (unit titles are title case)
        if not line_stripped[0].isupper():
            continue
        
        # Must NOT end with period (unit titles don't end with punctuation)
        if line_stripped.endswith('.') or line_stripped.endswith(','):
            continue
        
        # Must NOT be a sentence (check for verbs)
        if re.search(r'\s+(is|are|was|were|has|have|had|does|do|did|will|would|can|could|should|may|might|took|takes|taken)\s+', line_stripped, re.IGNORECASE):
            continue
        
        # Skip if it matches exclude patterns
        should_exclude = False
        for pattern in exclude_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # Must match one of the main unit patterns OR be a clear unit title
        topic_name = None
        word_count = len(line_stripped.split())
        
        # Check if it matches a main unit pattern
        for pattern in main_unit_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                topic_name = line_stripped
                break
        
        # If no pattern match, check if it looks like a unit title
        if not topic_name:
            # Must be 2-6 words (unit titles are concise)
            if not (2 <= word_count <= 6):
                continue
            
            # Must be title case or mostly capitalized (unit titles are formatted)
            words = line_stripped.split()
            title_case_count = sum(1 for w in words if w[0].isupper() if w)
            if title_case_count < len(words) * 0.5:  # At least half should be capitalized
                continue
            
            # Must contain curriculum-related keywords
            curriculum_keywords = [
                'quebec', 'canada', 'france', 'british', 'war', 'rights', 'civil',
                'indigenous', 'aboriginal', 'occupants', 'conquest', 'colonization',
                'contemporary', 'modernization', 'social', 'change', 'identity',
                'territory', 'population', 'settlement', 'region', 'geography',
                'resources', 'development', 'matter', 'energy', 'properties',
                'number', 'algebra', 'geometry', 'statistics', 'mathematics',
                'new france', 'world war', 'civil rights'
            ]
            line_lower = line_stripped.lower()
            has_curriculum_keyword = any(kw in line_lower for kw in curriculum_keywords)
            
            if not has_curriculum_keyword:
                continue
            
            # Must NOT be a fragment (check for incomplete phrases)
            if line_stripped.endswith(' of') or line_stripped.endswith(' in') or line_stripped.endswith(' the'):
                continue
            
            # Must NOT be a sub-item (already filtered by exclude_patterns, but double-check)
            if re.match(r'^[a-z][\.\)]\s+', line_stripped):
                continue
            
            topic_name = line_stripped
        
        if topic_name:
            # Clean up topic name
            topic_name = re.sub(r'\s+', ' ', topic_name).strip()
            
            # Normalize variations (e.g., "New France" vs "Nouvelle-France")
            topic_normalized = topic_name.lower()
            topic_normalized = re.sub(r'[^\w\s]', '', topic_normalized)  # Remove punctuation for comparison
            
            # Skip if we've seen a similar topic (avoid duplicates)
            if topic_normalized in seen_topics:
                continue
            
            seen_topics.add(topic_normalized)
            
            # For big unit topics, we don't need to extract concepts/objectives from surrounding text
            # Those will be in the curriculum document structure, not as fragments
            topics.append({
                'name': topic_name,
                'concepts': [],  # Keep empty - concepts should come from structured data, not fragments
                'learningObjectives': [],  # Keep empty - objectives should come from structured data
                'progression': {'buildsOn': [], 'preparesFor': []}
            })
    
    # STRICT Final filtering - only keep actual big unit topics
    filtered_topics = []
    excluded_phrases = [
        # Competency-related phrases (competencies are NOT topics)
        'competency', 'competence', 'compétence',
        'understands the', 'interprets', 'constructs',
        'understands the organization', 'interprets a territorial',
        'constructs his/her consciousness', 'constructs consciousness',
        'development of competency', 'competency development',
        
        # Other exclusions
        'differentiated', 'differentiation', 'adaptation', 'modification',
        'instruction', 'pedagogy', 'elements for', 'what that means',
        'some suggestions', 'implementing', 'expectations associated',
        'qep requirements', 'competency levels', 'secondary school',
        'programme de base', 'programme enrichi', 'acting to foster',
        'educational success', 'the educational', 'foster the',
        'concepts associated', 'with giftedness', 'gifted students',
        'taking giftedness', 'into account', 'in the', 'school context',
        'courses of action', 'to foster', 'the success', 'secondary education',
        'elementary and secondary', 'preschool education', 'preschool cycle',
        'secondary cycle', 'elementary cycle'
    ]
    
    # Subject-specific exclusions - filter out topics from other subjects
    if subject:
        if 'History' in subject or 'Citizenship' in subject:
            # History: exclude French, Geography, Science, Math topics
            excluded_phrases.extend(['français', 'langue seconde', 'immersion', 'languages', 'langues',
                                   'geography', 'géographie', 'science', 'mathematics', 'math', 'mathematique'])
        elif 'Geography' in subject:
            # Geography: exclude French, History, Science, Math topics
            excluded_phrases.extend(['français', 'langue seconde', 'immersion', 'languages', 'langues',
                                   'history', 'histoire', 'war', 'guerre', 'rights', 'droits',
                                   'science', 'mathematics', 'math', 'mathematique'])
        elif 'Science' in subject or 'Technology' in subject:
            # Science: exclude French, History, Geography, Math topics
            excluded_phrases.extend(['français', 'langue seconde', 'immersion', 'languages', 'langues',
                                   'history', 'histoire', 'war', 'guerre', 'geography', 'géographie',
                                   'mathematics', 'math', 'mathematique'])
        elif 'Mathematics' in subject or 'Math' in subject:
            # Math: exclude French, History, Geography, Science topics
            excluded_phrases.extend(['français', 'langue seconde', 'immersion', 'languages', 'langues',
                                   'history', 'histoire', 'war', 'guerre', 'geography', 'géographie',
                                   'science', 'technology', 'technologie'])
        elif 'English' in subject or 'Language' in subject:
            # Language Arts: exclude History, Geography, Science, Math topics
            excluded_phrases.extend(['history', 'histoire', 'war', 'guerre', 'geography', 'géographie',
                                   'science', 'mathematics', 'math', 'mathematique'])
    
    for topic in topics:
        name = topic['name']
        name_lower = name.lower()
        words = name_lower.split()
        
        # Must be 2-6 words (big unit topics are concise)
        if not (2 <= len(words) <= 6):
            continue
        
        # Must NOT contain excluded phrases
        if any(phrase in name_lower for phrase in excluded_phrases):
            continue
        
        # Must NOT be a sentence fragment (check for verbs, prepositions at end)
        if re.search(r'\s+(is|are|was|were|has|have|had|does|do|did|will|would|can|could|should|may|might|took|takes|taken|occurred|happened)\s+', name, re.IGNORECASE):
            continue
        
        # Must NOT be a question
        if name.endswith('?') or re.match(r'^(how|what|when|where|why|which|who)\s+', name_lower):
            continue
        
        # Must contain at least 2 meaningful content words
        structure_words = ['the', 'and', 'or', 'of', 'for', 'with', 'from', 'to', 'in', 'on', 'at', 'by', 'a', 'an']
        content_words = [w for w in words if w not in structure_words and len(w) > 3]
        if len(content_words) < 2:
            continue
        
        # Must contain curriculum-related keywords (big units always do)
        curriculum_keywords = [
            'quebec', 'canada', 'france', 'british', 'war', 'rights', 'civil',
            'indigenous', 'aboriginal', 'occupants', 'conquest', 'colonization',
            'contemporary', 'modernization', 'social', 'change', 'identity',
            'territory', 'population', 'settlement', 'region', 'geography',
            'resources', 'development', 'matter', 'energy', 'properties',
            'number', 'algebra', 'geometry', 'statistics', 'mathematics',
            'new france', 'world war', 'civil rights', 'first occupants'
        ]
        has_curriculum_keyword = any(kw in name_lower for kw in curriculum_keywords)
        if not has_curriculum_keyword:
            continue
        
        # Must look like a unit title (title case, no ending punctuation)
        if name.endswith('.') or name.endswith(',') or name.endswith(':'):
            continue
        
        filtered_topics.append(topic)
    
    # Remove duplicates and sort
    unique_topics = []
    seen_names = set()
    for topic in filtered_topics:
        name_normalized = re.sub(r'[^\w\s]', '', topic['name'].lower())
        if name_normalized not in seen_names:
            seen_names.add(name_normalized)
            unique_topics.append(topic)
    
    return unique_topics

def validate_topic_for_grade(topic_name: str, grade: str, subject: str) -> bool:
    """Validate that a topic is appropriate for the given grade level"""
    topic_lower = topic_name.lower()
    grade_num = None
    
    # Extract grade number if present
    if 'secondary' in grade.lower():
        match = re.search(r'secondary\s*(\d+)', grade.lower())
        if match:
            grade_num = int(match.group(1))
    
    # Grade-specific topic validation for History
    if subject == 'History and Citizenship Education' and grade_num:
        if grade_num == 3:
            # Sec 3 History topics are Quebec and Canada History (Origins to 1608, 1608-1760, 1760-1791, 1791-1840)
            # Accept topics that match the expected patterns for Sec 3
            sec3_patterns = [
                'origins to 1608', '1608-1760', '1760-1791', '1791-1840',
                'indigenous peoples', 'colonization', 'colonial society', 'french rule',
                'conquest', 'change of empire', 'demands', 'struggles', 'nationhood'
            ]
            
            # Accept if topic matches Sec 3 patterns
            matches_sec3 = any(pattern in topic_lower for pattern in sec3_patterns)
            # Reject topics from Sec 4 (1840+, 1896+, 1945+, 1980+)
            sec4_patterns = ['1840', '1896', '1945', '1980', 'canadian federal system', 
                           'nationalisms', 'autonomy of canada', 'quiet revolution',
                           'modernization of québec', 'contemporary québec']
            is_sec4 = any(pattern in topic_lower for pattern in sec4_patterns)
            
            return matches_sec3 and not is_sec4
        
        elif grade_num in [1, 2]:
            # Sec 1-2 History = Early periods
            appropriate = ['first occupants', 'new france', 'british rule', 'colonization', 
                          'conquest', 'indigenous', 'aboriginal']
            inappropriate = ['first world war', 'world war', 'wwi', 'wwii', 'civil rights',
                           'contemporary quebec', '20th century', 'modernization']
            
            has_appropriate = any(kw in topic_lower for kw in appropriate)
            has_inappropriate = any(kw in topic_lower for kw in inappropriate)
            
            return has_appropriate and not has_inappropriate
        
        elif grade_num in [4, 5]:
            # Sec 4-5 History = Modern periods
            appropriate = ['civil rights', 'rights and freedoms', 'contemporary', '20th century',
                         'first world war', 'second world war', 'wwi', 'wwii', 'modernization']
            inappropriate = ['first occupants', 'new france', 'british rule']
            
            has_appropriate = any(kw in topic_lower for kw in appropriate)
            has_inappropriate = any(kw in topic_lower for kw in inappropriate)
            
            return has_appropriate and not has_inappropriate
    
    # For other subjects or if no specific validation, allow the topic
    return True

def parse_curriculum_data(text: str, filename: str) -> List[Dict]:
    """Parse curriculum data from extracted text - returns list for multiple grades"""
    subject, grades_list = identify_subject_grade(filename, text)
    
    if not subject or not grades_list:
        return []
    
    competencies = extract_competencies(text)
    
    # Return one entry per grade with grade-appropriate topics
    results = []
    for grade in grades_list:
        # Extract topics with subject and grade context for better filtering
        # For History subjects, extraction is grade-specific, so extract per grade
        topics = extract_topics(text, grade=grade, subject=subject)
        
        # Filter topics to be grade-appropriate (for non-History subjects)
        grade_appropriate_topics = []
        for topic in topics:
            if validate_topic_for_grade(topic['name'], grade, subject):
                grade_appropriate_topics.append(topic)
        
        # Extract cross-curricular competencies and broad areas of learning for this grade
        cross_curricular = extract_cross_curricular_competencies(text, subject, grade)
        broad_areas = extract_broad_areas_of_learning(text, subject, grade)
        subject_themes = extract_subject_themes(text, subject, grade)
        
        results.append({
            'subject': subject,
            'grade': grade,
            'competencies': competencies,
            'topics': grade_appropriate_topics,
            'crossCurricularCompetencies': cross_curricular,
            'broadAreasOfLearning': broad_areas,
            'subjectThemes': subject_themes,
            'filename': filename
        })
    
    return results

def generate_js_structure(parsed_data_list: List[Dict]) -> str:
    """Generate JavaScript code for pfeqCurriculum structure"""
    # Organize by subject -> grade
    curriculum = {}
    
    # Known History topics - always add these
    history_topics = {
        'Secondary 1': [
            'Sedentarization',
            'The Emergence of Civilisations in Mesopotamia',
            'Athens: a First Experiment in Democracy',
            'Romanisation',
            'The Christianisation of the West in the Middle Ages',
            'The Growth of Cities and Trade'
        ],
        'Secondary 2': [
            'Renaissance: a New Vision of Man',
            'European Expansion Around the World',
            'The American and French Revolutions',
            'Industrialization: an Economic and Social Revolution',
            'The Expansion of the Industrial World',
            'Recognition of Civil Rights and Freedoms'
        ],
        'Secondary 3': [
            'Origins to 1608 The experience of the Indigenous peoples and the colonization attempts',
            '1608-1760 The evolution of colonial society under French rule',
            '1760-1791 The Conquest and the change of empire',
            '1791-1840 The demands and struggles of nationhood'
        ],
        'Secondary 4': [
            '1840-1896 The formation of the Canadian federal system',
            '1896-1945 Nationalisms and the autonomy of Canada',
            '1945-1980 The modernization of Québec and the Quiet Revolution',
            'From 1980 to our times Societal choices in contemporary Québec'
        ]
    }
    
    # Ensure History subject exists
    if 'History and Citizenship Education' not in curriculum:
        curriculum['History and Citizenship Education'] = {}
    
    # Add known History topics for each grade
    for grade, topic_names in history_topics.items():
        if grade not in curriculum['History and Citizenship Education']:
            curriculum['History and Citizenship Education'][grade] = {
                'competencies': [],
                'topics': [],
                'crossCurricularCompetencies': [],
                'broadAreasOfLearning': [],
                'subjectThemes': []
            }
        # Add topics if not already present
        existing_topic_names = {t['name'] for t in curriculum['History and Citizenship Education'][grade]['topics']}
        for topic_name in topic_names:
            if topic_name not in existing_topic_names:
                curriculum['History and Citizenship Education'][grade]['topics'].append({
                    'name': topic_name,
                    'concepts': [],
                    'learningObjectives': [],
                    'progression': {'buildsOn': [], 'preparesFor': []}
                })
    
    for data in parsed_data_list:
        if not data:
            continue
        
        subject = data['subject']
        grade = data['grade']
        
        if subject not in curriculum:
            curriculum[subject] = {}
        
        if grade not in curriculum[subject]:
            curriculum[subject][grade] = {
                'competencies': [],
                'topics': [],
                'crossCurricularCompetencies': [],
                'broadAreasOfLearning': [],
                'subjectThemes': []
            }
        
        # Merge competencies (avoid duplicates)
        existing_comp_ids = {c.get('id', '') for c in curriculum[subject][grade]['competencies']}
        for comp in data['competencies']:
            comp_id = comp.get('id', '')
            if comp_id and comp_id not in existing_comp_ids:
                curriculum[subject][grade]['competencies'].append(comp)
                existing_comp_ids.add(comp_id)
            elif not comp_id:
                # Add if no ID conflict
                curriculum[subject][grade]['competencies'].append(comp)
        
        # Merge topics (avoid duplicates by name)
        existing_topic_names = {t['name'] for t in curriculum[subject][grade]['topics']}
        for topic in data['topics']:
            if topic['name'] not in existing_topic_names:
                curriculum[subject][grade]['topics'].append(topic)
                existing_topic_names.add(topic['name'])
        
        # Merge cross-curricular competencies (avoid duplicates)
        existing_cross_curricular = set(curriculum[subject][grade]['crossCurricularCompetencies'])
        for comp in data.get('crossCurricularCompetencies', []):
            if comp not in existing_cross_curricular:
                curriculum[subject][grade]['crossCurricularCompetencies'].append(comp)
                existing_cross_curricular.add(comp)
        
        # Merge broad areas of learning (avoid duplicates)
        existing_broad_areas = set(curriculum[subject][grade]['broadAreasOfLearning'])
        for area in data.get('broadAreasOfLearning', []):
            if area not in existing_broad_areas:
                curriculum[subject][grade]['broadAreasOfLearning'].append(area)
                existing_broad_areas.add(area)
        
        # Merge subject themes (avoid duplicates)
        existing_themes = set(curriculum[subject][grade]['subjectThemes'])
        for theme in data.get('subjectThemes', []):
            if theme not in existing_themes:
                curriculum[subject][grade]['subjectThemes'].append(theme)
                existing_themes.add(theme)
    
    # Generate JavaScript code
    js_lines = ['const pfeqCurriculum = {', '    subjects: {']
    
    for subject, grades in sorted(curriculum.items()):
        js_lines.append(f'        "{subject}": {{')
        js_lines.append('            grades: {')
        
        for grade, data in sorted(grades.items()):
            js_lines.append(f'                "{grade}": {{')
            
            # Competencies
            js_lines.append('                    competencies: [')
            for comp in data['competencies']:
                js_lines.append('                        {')
                if comp.get('id'):
                    js_lines.append(f'                            id: "{comp["id"]}",')
                js_lines.append(f'                            name: {json.dumps(comp["name"])},')
                if comp.get('learningObjectives'):
                    js_lines.append('                            learningObjectives: [')
                    for obj in comp['learningObjectives']:
                        js_lines.append(f'                                {json.dumps(obj)},')
                    js_lines.append('                            ]')
                js_lines.append('                        },')
            js_lines.append('                    ],')
            
            # Topics
            js_lines.append('                    topics: [')
            for topic in data['topics']:
                js_lines.append('                        {')
                js_lines.append(f'                            name: {json.dumps(topic["name"])},')
                if topic.get('concepts'):
                    js_lines.append('                            concepts: [')
                    for concept in topic['concepts']:
                        js_lines.append(f'                                {json.dumps(concept)},')
                    js_lines.append('                            ],')
                if topic.get('learningObjectives'):
                    js_lines.append('                            learningObjectives: [')
                    for obj in topic['learningObjectives']:
                        js_lines.append(f'                                {json.dumps(obj)},')
                    js_lines.append('                            ],')
                if topic.get('progression'):
                    js_lines.append('                            progression: {')
                    if topic['progression'].get('buildsOn'):
                        js_lines.append('                                buildsOn: [')
                        for item in topic['progression']['buildsOn']:
                            js_lines.append(f'                                    {json.dumps(item)},')
                        js_lines.append('                                ],')
                    if topic['progression'].get('preparesFor'):
                        js_lines.append('                                preparesFor: [')
                        for item in topic['progression']['preparesFor']:
                            js_lines.append(f'                                    {json.dumps(item)},')
                        js_lines.append('                                ],')
                    js_lines.append('                            },')
                js_lines.append('                        },')
            js_lines.append('                    ],')
            
            # Cross-curricular competencies
            js_lines.append('                    crossCurricularCompetencies: [')
            for comp in data.get('crossCurricularCompetencies', []):
                js_lines.append(f'                        {json.dumps(comp)},')
            js_lines.append('                    ],')
            
            # Broad areas of learning
            js_lines.append('                    broadAreasOfLearning: [')
            for area in data.get('broadAreasOfLearning', []):
                js_lines.append(f'                        {json.dumps(area)},')
            js_lines.append('                    ],')
            
            # Subject themes
            js_lines.append('                    subjectThemes: [')
            for theme in data.get('subjectThemes', []):
                js_lines.append(f'                        {json.dumps(theme)},')
            js_lines.append('                    ]')
            
            js_lines.append('                },')
        
        js_lines.append('            }')
        js_lines.append('        },')
    
    js_lines.append('    }')
    js_lines.append('};')
    
    return '\n'.join(js_lines)

def process_all_pdfs(folder_path: str) -> str:
    """Process all PDFs in folder and generate JavaScript code - DEPRECATED, use main() instead"""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Folder not found: {folder_path}")
        return ""
    
    pdf_files = list(folder.glob('*.pdf'))
    print(f"Found {len(pdf_files)} PDF files")
    
    parsed_data_list = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Processing {i}/{len(pdf_files)}: {pdf_file.name}")
        try:
            text = extract_pdf_text(pdf_file)
            if not text or not isinstance(text, str) or len(text.strip()) < 100:
                print(f"  Warning: Little or no text extracted from {pdf_file.name}")
                continue
            
            parsed_data_list_items = parse_curriculum_data(text, pdf_file.name)
            if parsed_data_list_items:
                parsed_data_list.extend(parsed_data_list_items)
                for item in parsed_data_list_items:
                    print(f"  Extracted: {item['subject']} - {item['grade']}")
            else:
                print(f"  Could not identify subject/grade for {pdf_file.name}")
        except Exception as e:
            print(f"  Error processing {pdf_file.name}: {e}")
    
    if not parsed_data_list:
        print("No data extracted from any PDFs")
        return ""
    
    js_code = generate_js_structure(parsed_data_list)
    return js_code

if __name__ == '__main__':
    # Paths to PFEQ folders - check both original and complete download
    pfeq_folders = [
        r'c:\Users\johnn\Downloads\PFEQ',
        r'c:\Users\johnn\Downloads\PFEQ_Complete\preschool',
        r'c:\Users\johnn\Downloads\PFEQ_Complete\elementary',
        r'c:\Users\johnn\Downloads\PFEQ_Complete\secondary',
    ]
    
    print("Starting PFEQ PDF extraction...")
    all_parsed_data = []
    
    for folder in pfeq_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"\nProcessing folder: {folder}")
            parsed_data_list = []
            
            pdf_files = list(folder_path.glob('*.pdf'))
            print(f"Found {len(pdf_files)} PDF files")
            
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"Processing {i}/{len(pdf_files)}: {pdf_file.name}")
                try:
                    text = extract_pdf_text(pdf_file)
                    if not text or not isinstance(text, str) or len(text.strip()) < 100:
                        print(f"  Warning: Little or no text extracted from {pdf_file.name}")
                        continue
                    
                    parsed_data_list_items = parse_curriculum_data(text, pdf_file.name)
                    if parsed_data_list_items:
                        parsed_data_list.extend(parsed_data_list_items)
                        for item in parsed_data_list_items:
                            print(f"  Extracted: {item['subject']} - {item['grade']}")
                    else:
                        print(f"  Could not identify subject/grade for {pdf_file.name}")
                except Exception as e:
                    print(f"  Error processing {pdf_file.name}: {e}")
            
            all_parsed_data.extend(parsed_data_list)
    
    if all_parsed_data:
        js_output = generate_js_structure(all_parsed_data)
    else:
        js_output = ""
        print("No data extracted from any PDFs")
    
    if js_output:
        # Save to file
        output_file = Path(__file__).parent / 'pfeq_curriculum_data.js'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_output)
        print(f"\nJavaScript code saved to: {output_file}")
        print(f"\nGenerated {len(js_output)} characters of JavaScript code")
    else:
        print("\nNo data extracted. Please check the PDF files.")
