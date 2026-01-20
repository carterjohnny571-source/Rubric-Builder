#!/usr/bin/env python3
"""
Generate JavaScript curriculum data file from hardcoded curriculum data
This script reads curriculum_data.py and generates pfeq_curriculum_data.js
"""

import json
from pathlib import Path
from curriculum_data import CURRICULUM_DATA

def generate_js_structure(curriculum_data: dict) -> str:
    """Generate JavaScript code for pfeqCurriculum structure from hardcoded data"""
    js_lines = ['const pfeqCurriculum = {', '    subjects: {']
    
    for subject, grades in sorted(curriculum_data.items()):
        js_lines.append(f'        "{subject}": {{')
        js_lines.append('            grades: {')
        
        for grade, data in sorted(grades.items()):
            js_lines.append(f'                "{grade}": {{')
            
            # Competencies
            js_lines.append('                    competencies: [')
            for comp in data.get('competencies', []):
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
            for topic_name in data.get('topics', []):
                js_lines.append('                        {')
                js_lines.append(f'                            name: {json.dumps(topic_name)},')
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

if __name__ == '__main__':
    print("Generating JavaScript curriculum data file...")
    
    # Generate JS code from curriculum data
    js_output = generate_js_structure(CURRICULUM_DATA)
    
    if js_output:
        # Save to file
        output_file = Path(__file__).parent / 'pfeq_curriculum_data.js'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_output)
        print(f"JavaScript code saved to: {output_file}")
        print(f"Generated {len(js_output)} characters of JavaScript code")
        
        # Count subjects and grades
        subject_count = len(CURRICULUM_DATA)
        total_grades = sum(len(grades) for grades in CURRICULUM_DATA.values())
        print(f"Generated data for {subject_count} subject(s) and {total_grades} grade(s)")
    else:
        print("Error: Failed to generate JavaScript code")
