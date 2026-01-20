// Global state
let currentDate = new Date();
let currentView = 'month';
let selectedAssignment = null;
let editingStudentId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    loadScheduleConfig();
    loadStudents();
    loadRubrics();
    loadAssignments();
    renderCalendar();
    updateCurrentMonthDisplay();
    populateAssignmentSelect();
}

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Activate corresponding button
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach((btn, index) => {
        const tabNames = ['setup', 'calendar', 'students', 'rubrics', 'grades'];
        if (tabNames[index] === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Refresh data if needed
    if (tabName === 'calendar') {
        renderCalendar();
    } else if (tabName === 'students') {
        renderStudents();
    } else if (tabName === 'rubrics') {
        renderRubrics();
    }
}

// Schedule Configuration
function loadScheduleConfig() {
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    
    if (config.cycleLength) {
        document.getElementById('cycleLength').value = config.cycleLength;
    }
    if (config.startDate) {
        document.getElementById('startDate').value = config.startDate;
    }
    if (config.endDate) {
        document.getElementById('endDate').value = config.endDate;
    }
    
    renderScheduleGrid(config);
}

function renderScheduleGrid(config) {
    const cycleLength = parseInt(document.getElementById('cycleLength').value) || 9;
    const classSchedule = config.classSchedule || {};
    const grid = document.getElementById('scheduleGrid');
    grid.innerHTML = '';
    
    for (let i = 1; i <= cycleLength; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'schedule-day';
        dayDiv.innerHTML = `<h4>Day ${i}</h4><div id="day${i}Classes"></div>`;
        grid.appendChild(dayDiv);
        
        const classesDiv = document.getElementById(`day${i}Classes`);
        const classes = classSchedule[i] || [];
        
        classes.forEach((cls, index) => {
            const classItem = document.createElement('div');
            classItem.className = 'class-item';
            classItem.innerHTML = `
                <span>${cls}</span>
                <button onclick="removeClassFromDay(${i}, ${index})">×</button>
            `;
            classesDiv.appendChild(classItem);
        });
    }
}

function addClassToSchedule() {
    const day = prompt('Enter day number (1-' + document.getElementById('cycleLength').value + '):');
    if (!day) return;
    
    const dayNum = parseInt(day);
    const cycleLength = parseInt(document.getElementById('cycleLength').value);
    
    if (dayNum < 1 || dayNum > cycleLength) {
        alert('Invalid day number');
        return;
    }
    
    const className = prompt('Enter class name:');
    if (!className) return;
    
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    if (!config.classSchedule) config.classSchedule = {};
    if (!config.classSchedule[dayNum]) config.classSchedule[dayNum] = [];
    
    config.classSchedule[dayNum].push(className);
    localStorage.setItem('scheduleConfig', JSON.stringify(config));
    
    renderScheduleGrid(config);
}

function removeClassFromDay(day, index) {
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    if (config.classSchedule && config.classSchedule[day]) {
        config.classSchedule[day].splice(index, 1);
        localStorage.setItem('scheduleConfig', JSON.stringify(config));
        renderScheduleGrid(config);
    }
}

function updateScheduleConfig() {
    renderScheduleGrid(JSON.parse(localStorage.getItem('scheduleConfig') || '{}'));
}

function saveScheduleConfig() {
    const config = {
        cycleLength: parseInt(document.getElementById('cycleLength').value),
        startDate: document.getElementById('startDate').value,
        endDate: document.getElementById('endDate').value,
        classSchedule: JSON.parse(localStorage.getItem('scheduleConfig') || '{}').classSchedule || {}
    };
    
    localStorage.setItem('scheduleConfig', JSON.stringify(config));
    alert('Schedule configuration saved!');
}

function handleCalendarUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            let holidays = [];
            if (file.name.endsWith('.csv')) {
                holidays = parseCSVCalendar(e.target.result);
            } else if (file.name.endsWith('.json')) {
                holidays = JSON.parse(e.target.result);
            }
            
            const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
            config.holidays = holidays;
            localStorage.setItem('scheduleConfig', JSON.stringify(config));
            
            document.getElementById('calendarPreview').innerHTML = 
                `<p>Loaded ${holidays.length} holidays/non-instructional days</p>`;
            
            renderCalendar();
        } catch (error) {
            alert('Error parsing calendar file: ' + error.message);
        }
    };
    reader.readAsText(file);
}

function parseCSVCalendar(csvText) {
    const lines = csvText.split('\n');
    const holidays = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line) {
            const parts = line.split(',');
            if (parts[0]) {
                holidays.push(parts[0].trim());
            }
        }
    }
    
    return holidays;
}

// Calendar Functions
function renderCalendar() {
    const view = document.getElementById('viewMode').value || 'month';
    currentView = view;
    
    if (view === 'month') {
        renderMonthView();
    } else {
        renderWeekView();
    }
}

function renderMonthView() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - startDate.getDay());
    
    const assignments = JSON.parse(localStorage.getItem('assignments') || '[]');
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    const holidays = config.holidays || [];
    
    const calendarView = document.getElementById('calendarView');
    calendarView.innerHTML = '<div class="calendar-month"></div>';
    const monthDiv = calendarView.querySelector('.calendar-month');
    
    // Day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        monthDiv.appendChild(header);
    });
    
    // Calendar days
    const current = new Date(startDate);
    for (let i = 0; i < 42; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'calendar-day';
        
        const dayNum = current.getDate();
        const dateStr = formatDate(current);
        
        // Check if other month
        if (current.getMonth() !== month) {
            dayDiv.classList.add('other-month');
        }
        
        // Check if weekend
        if (current.getDay() === 0 || current.getDay() === 6) {
            dayDiv.classList.add('weekend');
        }
        
        // Check if holiday
        if (holidays.includes(dateStr)) {
            dayDiv.classList.add('holiday');
        }
        
        // Check if today
        const today = new Date();
        if (current.toDateString() === today.toDateString()) {
            dayDiv.classList.add('today');
        }
        
        dayDiv.innerHTML = `<div class="day-number">${dayNum}</div>`;
        
        // Add assignments for this date
        const dayAssignments = assignments.filter(a => a.dueDate === dateStr);
        dayAssignments.forEach(assignment => {
            const badge = document.createElement('div');
            badge.className = 'assignment-badge';
            badge.textContent = assignment.rubricTitle;
            badge.onclick = () => openGradeEntry(assignment.id);
            dayDiv.appendChild(badge);
        });
        
        dayDiv.onclick = () => assignRubricToDate(dateStr);
        monthDiv.appendChild(dayDiv);
        
        current.setDate(current.getDate() + 1);
    }
}

function renderWeekView() {
    // Week view implementation
    const calendarView = document.getElementById('calendarView');
    calendarView.innerHTML = '<p>Week view coming soon</p>';
}

function changeMonth(direction) {
    currentDate.setMonth(currentDate.getMonth() + direction);
    renderCalendar();
    updateCurrentMonthDisplay();
}

function showToday() {
    currentDate = new Date();
    renderCalendar();
    updateCurrentMonthDisplay();
}

function updateCurrentMonthDisplay() {
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    const month = monthNames[currentDate.getMonth()];
    const year = currentDate.getFullYear();
    document.getElementById('currentMonth').textContent = `${month} ${year}`;
}

function changeViewMode() {
    renderCalendar();
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function getCycleDay(date) {
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    const startDate = config.startDate ? new Date(config.startDate) : null;
    const cycleLength = config.cycleLength || 9;
    
    if (!startDate) return null;
    
    // Calculate days since start, excluding weekends and holidays
    let current = new Date(startDate);
    let dayCount = 1;
    const holidays = config.holidays || [];
    
    while (current < date) {
        const dateStr = formatDate(current);
        const dayOfWeek = current.getDay();
        
        // Skip weekends and holidays
        if (dayOfWeek !== 0 && dayOfWeek !== 6 && !holidays.includes(dateStr)) {
            dayCount++;
        }
        
        current.setDate(current.getDate() + 1);
    }
    
    // Calculate which cycle day this is
    const cycleDay = ((dayCount - 1) % cycleLength) + 1;
    return cycleDay;
}

function assignRubricToDate(dateStr) {
    document.getElementById('assignDueDate').value = dateStr;
    showModal('assignRubricModal');
    populateAssignRubricForm();
}

// Student Management
function loadStudents() {
    renderStudents();
}

function renderStudents() {
    const students = JSON.parse(localStorage.getItem('students') || '[]');
    const searchTerm = document.getElementById('studentSearch')?.value.toLowerCase() || '';
    const classFilter = document.getElementById('classFilter')?.value || '';
    
    let filtered = students.filter(s => {
        const matchesSearch = !searchTerm || s.name.toLowerCase().includes(searchTerm);
        const matchesClass = !classFilter || (s.classSections && s.classSections.includes(classFilter));
        return matchesSearch && matchesClass;
    });
    
    const studentsList = document.getElementById('studentsList');
    studentsList.innerHTML = '';
    
    if (filtered.length === 0) {
        studentsList.innerHTML = '<p class="empty-message">No students found. Add your first student!</p>';
        return;
    }
    
    filtered.forEach(student => {
        const card = document.createElement('div');
        card.className = 'student-card';
        card.innerHTML = `
            <h3>${student.name}</h3>
            ${student.id ? `<p>ID: ${student.id}</p>` : ''}
            ${student.classSections && student.classSections.length > 0 ? 
                `<p>Classes: ${student.classSections.join(', ')}</p>` : ''}
            <div class="card-actions">
                <button class="btn btn-primary" onclick="editStudent('${student.id}')">Edit</button>
                <button class="btn btn-danger" onclick="deleteStudent('${student.id}')">Delete</button>
            </div>
        `;
        studentsList.appendChild(card);
    });
    
    updateClassFilter();
}

function showAddStudentModal() {
    editingStudentId = null;
    document.getElementById('addStudentForm').reset();
    document.getElementById('classSectionsInput').innerHTML = '';
    showModal('addStudentModal');
}

function addClassSection() {
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Class section name';
    input.className = 'class-section-input';
    input.style.cssText = 'width: 100%; margin-top: 5px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';
    document.getElementById('classSectionsInput').appendChild(input);
}

function saveStudent(event) {
    event.preventDefault();
    
    const name = document.getElementById('studentName').value;
    const id = document.getElementById('studentId').value;
    const sectionInputs = document.querySelectorAll('.class-section-input');
    const classSections = Array.from(sectionInputs).map(input => input.value.trim()).filter(v => v);
    
    const student = {
        id: editingStudentId || Date.now().toString(),
        name: name,
        studentId: id,
        classSections: classSections,
        dateAdded: editingStudentId ? 
            JSON.parse(localStorage.getItem('students') || '[]').find(s => s.id === editingStudentId)?.dateAdded || new Date().toISOString() :
            new Date().toISOString()
    };
    
    let students = JSON.parse(localStorage.getItem('students') || '[]');
    
    if (editingStudentId) {
        const index = students.findIndex(s => s.id === editingStudentId);
        if (index >= 0) {
            students[index] = student;
        }
    } else {
        students.push(student);
    }
    
    localStorage.setItem('students', JSON.stringify(students));
    closeModal('addStudentModal');
    renderStudents();
}

function editStudent(id) {
    const students = JSON.parse(localStorage.getItem('students') || '[]');
    const student = students.find(s => s.id === id);
    if (!student) return;
    
    editingStudentId = id;
    document.getElementById('studentName').value = student.name;
    document.getElementById('studentId').value = student.studentId || '';
    
    const sectionsDiv = document.getElementById('classSectionsInput');
    sectionsDiv.innerHTML = '';
    (student.classSections || []).forEach(section => {
        const input = document.createElement('input');
        input.type = 'text';
        input.value = section;
        input.className = 'class-section-input';
        input.style.cssText = 'width: 100%; margin-top: 5px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';
        sectionsDiv.appendChild(input);
    });
    
    showModal('addStudentModal');
}

function deleteStudent(id) {
    if (!confirm('Are you sure you want to delete this student?')) return;
    
    let students = JSON.parse(localStorage.getItem('students') || '[]');
    students = students.filter(s => s.id !== id);
    localStorage.setItem('students', JSON.stringify(students));
    
    // Also remove grades for this student
    let grades = JSON.parse(localStorage.getItem('grades') || '{}');
    Object.keys(grades).forEach(assignmentId => {
        if (grades[assignmentId][id]) {
            delete grades[assignmentId][id];
        }
    });
    localStorage.setItem('grades', JSON.stringify(grades));
    
    renderStudents();
}

function filterStudents() {
    renderStudents();
}

function updateClassFilter() {
    const students = JSON.parse(localStorage.getItem('students') || '[]');
    const allSections = new Set();
    
    students.forEach(s => {
        (s.classSections || []).forEach(section => allSections.add(section));
    });
    
    const filterSelect = document.getElementById('classFilter');
    const currentValue = filterSelect.value;
    filterSelect.innerHTML = '<option value="">All Classes</option>';
    
    allSections.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        filterSelect.appendChild(option);
    });
    
    filterSelect.value = currentValue;
}

function importStudents() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const lines = e.target.result.split('\n');
                const students = [];
                
                for (let i = 1; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line) {
                        const parts = line.split(',');
                        if (parts[0]) {
                            students.push({
                                id: Date.now().toString() + i,
                                name: parts[0].trim(),
                                studentId: parts[1] ? parts[1].trim() : '',
                                classSections: parts[2] ? parts[2].split(';').map(s => s.trim()) : [],
                                dateAdded: new Date().toISOString()
                            });
                        }
                    }
                }
                
                const existing = JSON.parse(localStorage.getItem('students') || '[]');
                existing.push(...students);
                localStorage.setItem('students', JSON.stringify(existing));
                
                alert(`Imported ${students.length} students`);
                renderStudents();
            } catch (error) {
                alert('Error importing students: ' + error.message);
            }
        };
        reader.readAsText(file);
    };
    input.click();
}

function exportStudents() {
    const students = JSON.parse(localStorage.getItem('students') || '[]');
    let csv = 'Name,ID,Class Sections\n';
    
    students.forEach(s => {
        csv += `"${s.name}","${s.studentId || ''}","${(s.classSections || []).join(';')}"\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'students.csv';
    a.click();
    URL.revokeObjectURL(url);
}

// Rubric Management
function loadRubrics() {
    renderRubrics();
}

function renderRubrics() {
    const rubrics = JSON.parse(localStorage.getItem('savedRubrics') || '[]');
    const rubricsList = document.getElementById('rubricsList');
    rubricsList.innerHTML = '';
    
    if (rubrics.length === 0) {
        rubricsList.innerHTML = '<p class="empty-message">No saved rubrics. Create one in the Rubric Builder!</p>';
        return;
    }
    
    rubrics.forEach(rubric => {
        const card = document.createElement('div');
        card.className = 'rubric-card';
        card.innerHTML = `
            <h3>${rubric.title}</h3>
            <p>${rubric.taskDescription || 'No description'}</p>
            <p><strong>Criteria:</strong> ${rubric.criteria.length}</p>
            <p><strong>Levels:</strong> ${rubric.numLevels}</p>
            ${rubric.curriculum.subject ? `<p><strong>Subject:</strong> ${rubric.curriculum.subject}</p>` : ''}
            <p><small>Created: ${new Date(rubric.dateCreated).toLocaleDateString()}</small></p>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="assignRubric('${rubric.id}')">Assign</button>
                <button class="btn btn-secondary" onclick="loadRubricToBuilder('${rubric.id}')">Edit</button>
                <button class="btn btn-danger" onclick="deleteRubric('${rubric.id}')">Delete</button>
            </div>
        `;
        rubricsList.appendChild(card);
    });
}

function assignRubric(rubricId) {
    selectedAssignment = { rubricId: rubricId };
    populateAssignRubricForm();
    showModal('assignRubricModal');
}

function populateAssignRubricForm() {
    const rubrics = JSON.parse(localStorage.getItem('savedRubrics') || '[]');
    const select = document.getElementById('assignRubricSelect');
    select.innerHTML = '';
    
    rubrics.forEach(rubric => {
        const option = document.createElement('option');
        option.value = rubric.id;
        option.textContent = rubric.title;
        if (selectedAssignment && selectedAssignment.rubricId === rubric.id) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    // Populate class select
    const config = JSON.parse(localStorage.getItem('scheduleConfig') || '{}');
    const classSelect = document.getElementById('assignClass');
    classSelect.innerHTML = '';
    
    if (config.classSchedule) {
        const allClasses = new Set();
        Object.values(config.classSchedule).forEach(classes => {
            classes.forEach(cls => allClasses.add(cls));
        });
        
        allClasses.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls;
            option.textContent = cls;
            classSelect.appendChild(option);
        });
    }
}

function saveAssignment(event) {
    event.preventDefault();
    
    const rubricId = document.getElementById('assignRubricSelect').value;
    const dueDate = document.getElementById('assignDueDate').value;
    const classPeriod = document.getElementById('assignClass').value;
    const weight = parseFloat(document.getElementById('assignWeight').value) || 10;
    
    const rubrics = JSON.parse(localStorage.getItem('savedRubrics') || '[]');
    const rubric = rubrics.find(r => r.id === rubricId);
    if (!rubric) {
        alert('Rubric not found');
        return;
    }
    
    const assignment = {
        id: Date.now().toString(),
        rubricId: rubricId,
        rubricTitle: rubric.title,
        dueDate: dueDate,
        classPeriod: classPeriod,
        weight: weight,
        dateCreated: new Date().toISOString()
    };
    
    let assignments = JSON.parse(localStorage.getItem('assignments') || '[]');
    assignments.push(assignment);
    localStorage.setItem('assignments', JSON.stringify(assignments));
    
    closeModal('assignRubricModal');
    renderCalendar();
    populateAssignmentSelect();
    alert('Assignment created!');
}

function loadAssignments() {
    populateAssignmentSelect();
}

function populateAssignmentSelect() {
    const assignments = JSON.parse(localStorage.getItem('assignments') || '[]');
    const select = document.getElementById('assignmentSelect');
    select.innerHTML = '<option value="">Select Assignment</option>';
    
    assignments.forEach(assignment => {
        const option = document.createElement('option');
        option.value = assignment.id;
        option.textContent = `${assignment.rubricTitle} - ${assignment.dueDate} (${assignment.classPeriod})`;
        select.appendChild(option);
    });
}

function loadRubricToBuilder(rubricId) {
    localStorage.setItem('loadRubricId', rubricId);
    window.location.href = 'rubric-builder.html';
}

function deleteRubric(id) {
    if (!confirm('Are you sure you want to delete this rubric?')) return;
    
    let rubrics = JSON.parse(localStorage.getItem('savedRubrics') || '[]');
    rubrics = rubrics.filter(r => r.id !== id);
    localStorage.setItem('savedRubrics', JSON.stringify(rubrics));
    
    // Also remove assignments using this rubric
    let assignments = JSON.parse(localStorage.getItem('assignments') || '[]');
    assignments = assignments.filter(a => a.rubricId !== id);
    localStorage.setItem('assignments', JSON.stringify(assignments));
    
    renderRubrics();
    populateAssignmentSelect();
}

// Grade Collection
function loadAssignmentGrades() {
    const assignmentId = document.getElementById('assignmentSelect').value;
    if (!assignmentId) {
        document.getElementById('gradeEntryArea').innerHTML = '<p class="empty-message">Select an assignment to begin grading</p>';
        return;
    }
    
    const assignments = JSON.parse(localStorage.getItem('assignments') || '[]');
    const assignment = assignments.find(a => a.id === assignmentId);
    if (!assignment) return;
    
    const rubrics = JSON.parse(localStorage.getItem('savedRubrics') || '[]');
    const rubric = rubrics.find(r => r.id === assignment.rubricId);
    if (!rubric) return;
    
    selectedAssignment = assignment;
    
    renderGradeEntryInterface(assignment, rubric);
}

function renderGradeEntryInterface(assignment, rubric) {
    const students = JSON.parse(localStorage.getItem('students') || '[]');
    const grades = JSON.parse(localStorage.getItem('grades') || '{}');
    const assignmentGrades = grades[assignment.id] || {};
    
    let html = `
        <div class="assignment-info">
            <h3>${assignment.rubricTitle}</h3>
            <p><strong>Due Date:</strong> ${assignment.dueDate}</p>
            <p><strong>Class:</strong> ${assignment.classPeriod}</p>
            <p><strong>Weight:</strong> ${assignment.weight}%</p>
        </div>
        <table class="grade-table">
            <thead>
                <tr>
                    <th>Student</th>
    `;
    
    // Add competency columns
    rubric.criteria.forEach((criterion, index) => {
        html += `<th class="competency-column">${criterion.name}</th>`;
    });
    html += `<th>Overall</th></tr></thead><tbody>`;
    
    // Add student rows
    students.forEach(student => {
        html += `<tr><td><strong>${student.name}</strong></td>`;
        
        let totalScore = 0;
        let totalWeight = 0;
        
        rubric.criteria.forEach((criterion, cIndex) => {
            const gradeKey = `${student.id}_${cIndex}`;
            const grade = assignmentGrades[gradeKey] || '';
            const levelIndex = grade ? parseInt(grade) : null;
            const score = levelIndex !== null ? ((levelIndex + 1) / rubric.numLevels) * 100 : null;
            
            if (score !== null) {
                totalScore += score;
                totalWeight += 1;
            }
            
            html += `<td>
                <select class="grade-input" onchange="saveGrade('${assignment.id}', '${student.id}', ${cIndex}, this.value)">
                    <option value="">--</option>
            `;
            
            rubric.levelNames.forEach((levelName, lIndex) => {
                html += `<option value="${lIndex}" ${grade == lIndex ? 'selected' : ''}>${levelName}</option>`;
            });
            
            html += `</select></td>`;
        });
        
        const overall = totalWeight > 0 ? (totalScore / totalWeight).toFixed(1) : '--';
        html += `<td><strong>${overall}%</strong></td></tr>`;
    });
    
    html += `</tbody></table>`;
    
    document.getElementById('gradeEntryArea').innerHTML = html;
}

function saveGrade(assignmentId, studentId, criterionIndex, levelIndex) {
    let grades = JSON.parse(localStorage.getItem('grades') || '{}');
    if (!grades[assignmentId]) {
        grades[assignmentId] = {};
    }
    
    const gradeKey = `${studentId}_${criterionIndex}`;
    if (levelIndex === '') {
        delete grades[assignmentId][gradeKey];
    } else {
        grades[assignmentId][gradeKey] = levelIndex;
    }
    
    localStorage.setItem('grades', JSON.stringify(grades));
    
    // Refresh the display
    loadAssignmentGrades();
}

function openGradeEntry(assignmentId) {
    document.getElementById('assignmentSelect').value = assignmentId;
    loadAssignmentGrades();
    showTab('grades');
}

// Modal Management
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
