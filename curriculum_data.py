#!/usr/bin/env python3
"""
Hardcoded Quebec Secondary Curriculum Data
This file contains curriculum data (topics, competencies) for secondary grades (1-5)
"""

# Standard Quebec PFEQ Cross-Curricular Competencies (same for all subjects/grades)
STANDARD_CROSS_CURRICULAR_COMPETENCIES = [
    "Uses information",
    "Exercises critical judgment",
    "Communicates appropriately",
    "Adopts effective work methods",
    "Cooperates"
]

# Standard Quebec PFEQ Broad Areas of Learning (same for all subjects/grades)
STANDARD_BROAD_AREAS_OF_LEARNING = [
    "Health and Well-Being",
    "Personal and Career Planning",
    "Environmental Awareness and Consumer Rights and Responsibilities",
    "Media Literacy",
    "Citizenship and Community Life"
]

# History-specific Competencies (same for all History grades)
HISTORY_COMPETENCIES = [
    {"id": "C1", "name": "Characterizes a period in the history of Quebec and Canada"},
    {"id": "C2", "name": "Interprets social phenomena using the historical method"},
    {"id": "C3", "name": "Constructs his/her consciousness of citizenship through the study of history"}
]

# History-specific Themes
HISTORY_THEMES = [
    "Quebec Identity",
    "Contemporary Quebec",
    "Modern Quebec",
    "Contemporary Issues",
    "Conquest",
    "New France",
    "First Occupants",
    "Quebec Modernization",
    "Civil Rights",
    "Colonization",
    "British Rule",
    "20th Century",
    "Rights and Freedoms"
]

# Geography-specific Competencies (same for both Secondary 1 and 2)
GEOGRAPHY_COMPETENCIES = [
    {"id": "C1", "name": "Understands the organization of a territory"},
    {"id": "C2", "name": "Interprets a territorial issue"},
    {"id": "C3", "name": "Constructs his/her consciousness of global citizenship"}
]

# Geography topics (all topics available for both Secondary 1 and 2)
GEOGRAPHY_TOPICS = [
    "Urban territory",
    "Metropolises",
    "Cities subject to natural hazards",
    "Heritage cities",
    "Regional territory",
    "Tourist regions",
    "Forest regions",
    "Energy-producing regions",
    "Industrial regions",
    "Agricultural territory",
    "Agricultural territory in a national space",
    "Agricultural territory subject to natural hazards",
    "Native territory",
    "Protected territory"
]

CURRICULUM_DATA = {
    'History and Citizenship Education': {
        'Secondary 1': {
            'topics': [
                'Sedentarization',
                'The Emergence of Civilisations in Mesopotamia',
                'Athens: a First Experiment in Democracy',
                'Romanisation',
                'The Christianisation of the West in the Middle Ages',
                'The Growth of Cities and Trade'
            ],
            'competencies': HISTORY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': HISTORY_THEMES
        },
        'Secondary 2': {
            'topics': [
                'Renaissance: a New Vision of Man',
                'European Expansion Around the World',
                'The American and French Revolutions',
                'Industrialization: an Economic and Social Revolution',
                'The Expansion of the Industrial World',
                'Recognition of Civil Rights and Freedoms'
            ],
            'competencies': HISTORY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': HISTORY_THEMES
        },
        'Secondary 3': {
            'topics': [
                'Origins to 1608: The experience of the Indigenous peoples and the colonization attempts',
                '1608-1760: The evolution of colonial society under French rule',
                '1760-1791: The Conquest and the change of empire',
                '1791-1840: The demands and struggles of nationhood'
            ],
            'competencies': HISTORY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': HISTORY_THEMES
        },
        'Secondary 4': {
            'topics': [
                '1840-1896: The formation of the Canadian federal system',
                '1896-1945: Nationalisms and the autonomy of Canada',
                '1945-1980: The modernization of Québec and the Quiet Revolution',
                'From 1980 to our times: Societal choices in contemporary Québec'
            ],
            'competencies': HISTORY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': HISTORY_THEMES
        },
        'Secondary 5': {
            'topics': [
                'Population',
                'Tensions and Conflicts',
                'Wealth'
            ],
            'competencies': HISTORY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': HISTORY_THEMES
        }
    },
    'Geography and Citizenship Education': {
        'Secondary 1': {
            'topics': GEOGRAPHY_TOPICS,
            'competencies': GEOGRAPHY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': []
        },
        'Secondary 2': {
            'topics': GEOGRAPHY_TOPICS,
            'competencies': GEOGRAPHY_COMPETENCIES,
            'crossCurricularCompetencies': STANDARD_CROSS_CURRICULAR_COMPETENCIES,
            'broadAreasOfLearning': STANDARD_BROAD_AREAS_OF_LEARNING,
            'subjectThemes': []
        }
    }
    # Other subjects (Science, Mathematics, English Language Arts) will be added when user provides them
}
