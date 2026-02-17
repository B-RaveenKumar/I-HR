/**
 * Timetable Management JavaScript - School Admin Panel
 * Handles period management, department permissions, and staff assignments
 */

let schoolId = null;
let allPeriods = [];
let allDepartments = [];
let allStaff = [];
let allLevels = [];
let allSections = [];
let currentAssignments = [];
let currentLevelFilter = null; // Track selected academic level

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // Use the schoolId initialized in HTML (from Flask session)
    schoolId = window.schoolId;
    console.log('🏫 Timetable Management initialized with school_id:', schoolId);

    // Check if user is authenticated and load data
    console.log('Starting data load...');
    loadAcademicLevels();
    loadAllSections();
    loadPeriods();
    loadDepartments();
    loadStaffList();
    loadStaffAssignmentsSummary();
});

// ==========================================================================
// PERIODS MANAGEMENT
// ==========================================================================

function loadPeriods() {
    console.log('Loading periods for school_id:', schoolId);
    const levelId = document.getElementById('filterGrade')?.value;
    const sectionId = document.getElementById('filterSection')?.value;
    const dayOfWeek = document.getElementById('filterDay')?.value;

    let url = `/api/timetable/periods?school_id=${schoolId}`;
    if (levelId) url += `&level_id=${levelId}`;
    if (sectionId) url += `&section_id=${sectionId}`;
    if (dayOfWeek) url += `&day_of_week=${dayOfWeek}`;

    fetch(url)
        .then(r => {
            console.log('Periods API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Periods data received:', data);
            allPeriods = data.periods || [];
            console.log(`Loaded ${allPeriods.length} periods`);
            renderPeriodsTable();
        })
        .catch(err => {
            console.error('Error loading periods:', err);
            showAlert('Failed to load periods: ' + err.message, 'error');
        });
}

function onFilterGradeChange() {
    const levelId = document.getElementById('filterGrade').value;
    const sectionSelect = document.getElementById('filterSection');

    // Remember currently selected section if any
    const currentSectionId = sectionSelect.value;

    sectionSelect.innerHTML = '<option value="">All Sections</option>';

    let sectionsToShow = allSections;
    if (levelId) {
        sectionsToShow = allSections.filter(s => s.level_id == levelId);
    }

    sectionSelect.innerHTML += sectionsToShow.map(s =>
        `<option value="${s.id}">${s.section_name}</option>`
    ).join('');

    // If the previously selected section is still in the list, keep it
    if (currentSectionId && sectionsToShow.find(s => s.id == currentSectionId)) {
        sectionSelect.value = currentSectionId;
    }

    loadPeriods();
}

function renderPeriodsTable() {
    const tbody = document.getElementById('periodsTableBody');

    if (allPeriods.length === 0) {
        tbody.innerHTML = '<tr style="background: #f8f9fa;"><td colspan="8" style="padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No periods defined. Add one to get started!</td></tr>';
        return;
    }

    tbody.innerHTML = allPeriods.map(p => {
        const level = allLevels.find(l => l.id == p.level_id);
        const section = allSections.find(s => s.id == p.section_id);
        const gsLabel = level ? `${level.level_name} - ${section ? section.section_name : 'All'}` : 'Global';

        const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const dayLabel = p.day_of_week !== null && p.day_of_week !== undefined ? DAYS[p.day_of_week] : 'All Days';

        return `
            <tr>
                <td style="padding: 1rem;">
                    <div>${gsLabel}</div>
                    <small class="text-muted"><i class="bi bi-calendar2-week"></i> ${dayLabel}</small>
                </td>
                <td style="padding: 1rem; font-weight: 600;">${p.period_number}</td>
                <td style="padding: 1rem;">${p.period_name || '-'}</td>
                <td style="padding: 1rem;"><span class="time-display">${p.start_time}</span></td>
                <td style="padding: 1rem;"><span class="time-display">${p.end_time}</span></td>
                <td style="padding: 1rem;"><span class="duration-badge">${p.duration_minutes} mins</span></td>
                <td style="padding: 1rem; text-align: center;">
                    <div class="action-buttons">
                        <button class="btn-edit btn-sm" onclick="editPeriod(${p.id})">
                            <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button class="btn-delete-action btn-sm" onclick="deletePeriod(${p.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function showAddPeriodModal() {
    document.getElementById('periodGrade').value = '';
    document.getElementById('periodSection').innerHTML = '<option value="">-- Select Section --</option>';
    document.getElementById('periodDay').value = '';
    document.getElementById('periodNumber').value = '';
    document.getElementById('periodName').value = '';
    document.getElementById('startTime').value = '';
    document.getElementById('endTime').value = '';
    document.getElementById('periodModalTitle').textContent = 'Add Period';
    document.getElementById('periodModal').dataset.editId = '';

    document.getElementById('duplicateAlert').classList.add('d-none');
    document.getElementById('quickFillContainer').classList.add('d-none');

    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function editPeriod(periodId) {
    const period = allPeriods.find(p => p.id === periodId);
    if (!period) return;

    document.getElementById('periodGrade').value = period.level_id || '';
    onPeriodGradeChange(period.section_id);

    document.getElementById('periodDay').value = period.day_of_week === null || period.day_of_week === undefined ? '' : period.day_of_week;
    document.getElementById('periodNumber').value = period.period_number;
    document.getElementById('periodName').value = period.period_name || '';
    document.getElementById('startTime').value = period.start_time;
    document.getElementById('endTime').value = period.end_time;
    document.getElementById('periodModalTitle').textContent = 'Edit Period';
    document.getElementById('periodModal').dataset.editId = periodId;

    document.getElementById('duplicateAlert').classList.add('d-none');
    document.getElementById('quickFillContainer').classList.add('d-none');

    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function savePeriod() {
    const levelId = document.getElementById('periodGrade').value;
    const sectionId = document.getElementById('periodSection').value;
    const dayOfWeek = document.getElementById('periodDay').value;
    const periodNumber = document.getElementById('periodNumber').value;
    const periodName = document.getElementById('periodName').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const editId = document.getElementById('periodModal').dataset.editId;

    if (!periodNumber || !startTime || !endTime) {
        showAlert('Please fill all required fields', 'error');
        return;
    }

    const data = {
        school_id: schoolId,
        level_id: levelId || null,
        section_id: sectionId || null,
        day_of_week: dayOfWeek === '' ? null : parseInt(dayOfWeek),
        period_number: parseInt(periodNumber),
        period_name: periodName,
        start_time: startTime,
        end_time: endTime
    };

    // Include ID if editing
    if (editId && editId !== '') {
        data.id = parseInt(editId);
    }

    fetch('/api/timetable/period/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Period saved successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('periodModal'));
                modal.hide();
                // Clear the editId after successful save
                delete document.getElementById('periodModal').dataset.editId;
                loadPeriods();
            } else {
                showAlert(result.error || 'Failed to save period', 'error');
            }
        })
        .catch(err => showAlert('Error saving period: ' + err.message, 'error'));
}

// ==========================================================================
// HIERARCHICAL DYNAMIC LOGIC
// ==========================================================================

// ==========================================================================
// HIERARCHICAL DYNAMIC LOGIC & MANAGEMENT
// ==========================================================================

function loadAcademicLevels() {
    fetch('/api/hierarchical-timetable/levels')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                allLevels = data.data;
                const filterGrade = document.getElementById('filterGrade');
                const periodGrade = document.getElementById('periodGrade');
                const sectionLevel = document.getElementById('sectionLevelId');
                const gradeSelectAssign = document.getElementById('gradeSelectAssign');

                const options = allLevels.map(l => `<option value="${l.id}">${l.level_name}</option>`).join('');

                if (filterGrade) filterGrade.innerHTML = '<option value="">All Grades</option>' + options;
                if (periodGrade) periodGrade.innerHTML = '<option value="">-- Select Grade --</option>' + options;
                if (sectionLevel) sectionLevel.innerHTML = '<option value="">-- Choose Grade --</option>' + options;
                if (gradeSelectAssign) gradeSelectAssign.innerHTML = '<option value="">-- Choose Grade --</option>' + options;

                renderLevelsList();

                // Re-apply filter highlight if active
                if (currentLevelFilter) {
                    filterSectionsByLevel(currentLevelFilter);
                }

                fetchOrgConfig();
            }
        });
}

function fetchOrgConfig() {
    fetch('/api/hierarchical-timetable/organization/config')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const orgType = data.data.organization_type;
                const badge = document.getElementById('orgTypeBadge');
                if (badge) {
                    badge.textContent = orgType.charAt(0).toUpperCase() + orgType.slice(1);
                    badge.className = orgType === 'school' ? 'badge bg-primary shadow-sm' : 'badge bg-info text-dark shadow-sm';
                }
                const radio = document.querySelector(`input[name="orgType"][value="${orgType}"]`);
                if (radio) radio.checked = true;
            }
        });
}

function renderLevelsList() {
    const container = document.getElementById('levelsListContainer');
    if (!container) return;

    if (allLevels.length === 0) {
        container.innerHTML = '<div class="p-4 text-center text-muted">No levels generated. Set Org Type first.</div>';
        return;
    }

    container.innerHTML = allLevels.map(level => `
        <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center level-item border-start-0 border-end-0" 
             style="cursor: pointer; padding: 1rem;" onclick="filterSectionsByLevel(${level.id}, this)">
            <div class="d-flex align-items-center flex-grow-1">
                <div class="me-3">
                   <span class="fw-600 d-block">${level.level_name}</span>
                   <small class="text-muted" style="font-size: 0.75rem;">${level.description || ''}</small>
                </div>
                <button class="btn btn-sm btn-outline-secondary ms-auto me-2 border-0 opacity-50 hover-opacity-100" 
                        onclick="event.stopPropagation(); editLevel(${level.id})" title="Edit Grade Name">
                    <i class="bi bi-pencil-square"></i>
                </button>
            </div>
            <i class="bi bi-chevron-right text-muted small"></i>
        </div>
    `).join('');
}

function editLevel(levelId) {
    const level = allLevels.find(l => l.id == levelId);
    if (!level) return;

    document.getElementById('editLevelId').value = level.id;
    document.getElementById('editLevelName').value = level.level_name;
    document.getElementById('editLevelDescription').value = level.description || '';

    new bootstrap.Modal(document.getElementById('editLevelModal')).show();
}

function updateLevel() {
    const levelId = document.getElementById('editLevelId').value;
    const levelName = document.getElementById('editLevelName').value;
    const description = document.getElementById('editLevelDescription').value;

    if (!levelName) {
        showAlert('Grade name is required', 'error');
        return;
    }

    fetch(`/api/hierarchical-timetable/levels/update/${levelId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            level_name: levelName,
            description: description
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Grade updated successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editLevelModal'));
                if (modal) modal.hide();
                loadAcademicLevels(); // Refresh lists
            } else {
                showAlert(data.error || 'Failed to update grade', 'error');
            }
        })
        .catch(err => console.error('Error updating level:', err));
}

function loadAllSections() {
    console.log('🔄 Loading all sections...');
    fetch('/api/hierarchical-timetable/sections/all')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                allSections = data.data;
                console.log(`✅ Loaded ${allSections.length} sections`);

                // Update filter dropdowns for Periods Management
                const filterSection = document.getElementById('filterSection');
                if (filterSection) {
                    const options = allSections.map(s => `<option value="${s.id}" data-level="${s.level_id}">${s.section_name}</option>`).join('');
                    filterSection.innerHTML = '<option value="">All Sections</option>' + options;
                }

                // Reload section management table using current filter
                renderSectionsTable(currentLevelFilter);
            }
        })
        .catch(err => console.error('❌ Error loading sections:', err));
}

function renderSectionsTable(levelId = null) {
    const tbody = document.getElementById('sectionsManagementBody');
    if (!tbody) return;

    let sectionsToShow = allSections;
    if (levelId) {
        sectionsToShow = allSections.filter(s => s.level_id == levelId);
    }

    if (sectionsToShow.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center p-4 text-muted">
            <div class="py-2">
                <i class="bi bi-info-circle fs-4 d-block mb-2"></i>
                No sections ${levelId ? 'found for this grade' : 'added yet'}.
            </div>
        </td></tr>`;
        return;
    }

    tbody.innerHTML = sectionsToShow.map(s => {
        const level = allLevels.find(l => l.id == s.level_id);
        return `
            <tr>
                <td style="padding: 0.75rem 1rem;">
                    <span class="badge bg-light text-dark border">${level ? level.level_name : 'Unknown'}</span>
                </td>
                <td style="padding: 0.75rem 1rem; font-weight: 600;">${s.section_name}</td>
                <td style="padding: 0.75rem 1rem;">${s.capacity} Students</td>
                <td style="padding: 0.75rem 1rem; text-align: center;">
                    <button class="btn btn-sm text-danger hover-grow" onclick="deleteSection(${s.id})" title="Delete Section">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterSectionsByLevel(levelId, element) {
    console.log('🎯 Filtering sections by level:', levelId);
    currentLevelFilter = levelId;

    // Basic highlight
    document.querySelectorAll('.level-item').forEach(el => el.classList.remove('active', 'bg-light'));
    if (element) {
        element.classList.add('bg-light');
    } else {
        // Find element if not passed (useful for re-applying highlight after reload)
        const items = document.querySelectorAll('.level-item');
        allLevels.forEach((l, idx) => {
            if (l.id == levelId && items[idx]) items[idx].classList.add('bg-light');
        });
    }

    renderSectionsTable(levelId);
}

function showOrgConfigModal() {
    new bootstrap.Modal(document.getElementById('orgConfigModal')).show();
}

function saveOrgType() {
    const orgType = document.querySelector('input[name="orgType"]:checked').value;

    fetch('/api/hierarchical-timetable/organization/set-type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({ organization_type: orgType })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert(`Successfully configured as ${orgType}`, 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('orgConfigModal'));
                if (modal) modal.hide();
                loadAcademicLevels();
            } else {
                showAlert(data.error || 'Failed to save configuration', 'error');
            }
        });
}

function showAddSectionModal() {
    const form = document.getElementById('sectionForm');
    if (form) form.reset();

    // Auto-populate level if one is selected on the left
    if (currentLevelFilter) {
        const levelSelect = document.getElementById('sectionLevelId');
        if (levelSelect) levelSelect.value = currentLevelFilter;
    }

    const modalEl = document.getElementById('sectionModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    modal.show();
}

function saveSection() {
    const levelId = document.getElementById('sectionLevelId').value;
    const sectionName = document.getElementById('sectionName').value;
    const capacity = document.getElementById('sectionCapacity').value;

    if (!levelId || !sectionName) {
        showAlert('Please select a grade and enter a section name', 'error');
        return;
    }

    fetch('/api/hierarchical-timetable/sections/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            level_id: parseInt(levelId),
            section_name: sectionName,
            capacity: parseInt(capacity)
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Section created successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('sectionModal'));
                if (modal) modal.hide();
                loadAllSections();
            } else {
                showAlert(data.error || 'Failed to create section', 'error');
            }
        });
}

function deleteSection(sectionId) {
    if (!confirm('Are you sure you want to delete this section? This will not work if there are active assignments.')) return;

    fetch(`/api/hierarchical-timetable/sections/${sectionId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Section deleted successfully', 'success');
                loadAllSections();
            } else {
                showAlert(data.error || 'Failed to delete section', 'error');
            }
        });
}

function onPeriodGradeChange(selectedSectionId = null) {
    const levelId = document.getElementById('periodGrade').value;
    const sectionSelect = document.getElementById('periodSection');

    sectionSelect.innerHTML = '<option value="">-- Select Section --</option>';

    if (levelId) {
        const filtered = allSections.filter(s => s.level_id == levelId);
        sectionSelect.innerHTML += filtered.map(s => `<option value="${s.id}">${s.section_name}</option>`).join('');
        if (selectedSectionId) sectionSelect.value = selectedSectionId;
    }

    fetchNextPeriodNumber();
}

function onPeriodSectionChange() {
    fetchNextPeriodNumber();
    checkDuplicatePeriodName();
}

/**
 * Handle Grade change in Staff Assignment section (Step 2)
 */
/**
 * Handle Grade change in Staff Assignment section (Step 2)
 */
function onAssignGradeChange() {
    const levelId = document.getElementById('gradeSelectAssign').value;
    const sectionSelect = document.getElementById('sectionSelectAssign');

    // Reset subsequent dropdowns
    sectionSelect.innerHTML = '<option value="">-- Choose Section --</option>';
    document.getElementById('periodSelectAssign').innerHTML = '<option value="">-- Choose Period --</option>';

    if (levelId) {
        const filtered = allSections.filter(s => s.level_id == levelId);
        sectionSelect.innerHTML += filtered.map(s => `<option value="${s.id}">${s.section_name}</option>`).join('');
    }
}

/**
 * Handle Section change in Staff Assignment section (Step 2)
 */
function onAssignSectionChange() {
    refreshAssignablePeriods();
}

/**
 * Handle Day change in Staff Assignment section (Step 2)
 */
function onAssignDayChange() {
    refreshAssignablePeriods();
}

/**
 * intelligently fetch and display periods based on selected filters
 * Shows: Defined periods for Day/Grade/Section
 * Filters: Marks as "Busy" if Section has class or Staff has class
 */
function refreshAssignablePeriods() {
    const staffId = document.getElementById('staffSelectAssign')?.value;
    const dayOfWeek = document.getElementById('daySelectAssign')?.value;
    const levelId = document.getElementById('gradeSelectAssign')?.value;
    const sectionId = document.getElementById('sectionSelectAssign')?.value;
    const periodSelect = document.getElementById('periodSelectAssign');

    periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';

    if (!staffId || !dayOfWeek || !levelId || !sectionId) {
        return; // Wait for all selections
    }

    periodSelect.innerHTML = '<option value="">Loading...</option>';

    // Fetch necessary data in parallel
    Promise.all([
        // 1. Get defined periods for this specific scenario
        fetch(`/api/timetable/periods?school_id=${schoolId}&level_id=${levelId}&section_id=${sectionId}&day_of_week=${dayOfWeek}`).then(r => r.json()),

        // 2. Get schedule for this section (to see if section is busy)
        fetch(`/api/hierarchical-timetable/section-schedule/${sectionId}`).then(r => r.json()),

        // 3. Get schedule for this staff (to see if staff is busy)
        fetch(`/api/hierarchical-timetable/staff-schedule/${staffId}`).then(r => r.json())
    ])
        .then(([periodsData, sectionData, staffData]) => {
            periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';

            const periods = periodsData.periods || [];
            const sectionSchedule = sectionData.success ? sectionData.data.schedule : [];
            const staffSchedule = staffData.success ? staffData.data.schedule : [];

            // Convert dayOfWeek to integer for comparison
            const dayInt = parseInt(dayOfWeek);

            if (periods.length === 0) {
                periodSelect.innerHTML = '<option value="">No periods defined for this day</option>';
                document.getElementById('staffAvailabilitySummary').classList.add('d-none');
                return;
            }

            // Filter schedules for the selected day
            const sectionBusyPeriods = sectionSchedule
                .filter(s => s.day_of_week === dayInt)
                .map(s => s.period_number);

            const staffBusyPeriods = staffSchedule
                .filter(s => s.day_of_week === dayInt)
                .map(s => s.period_number);

            // Calculate free periods for summary
            const allDayPeriods = periods.map(p => p.period_number);
            const freePeriods = allDayPeriods.filter(pNum => !staffBusyPeriods.includes(pNum));

            // Update Summary Display
            const summaryDiv = document.getElementById('staffAvailabilitySummary');
            if (summaryDiv) {
                summaryDiv.classList.remove('d-none');
                if (freePeriods.length > 0) {
                    summaryDiv.className = 'alert alert-info border';
                    summaryDiv.innerHTML = `<strong><i class="bi bi-calendar-check"></i> Staff Free Periods:</strong> ${freePeriods.join(', ')}`;
                } else {
                    summaryDiv.className = 'alert alert-warning border';
                    summaryDiv.innerHTML = `<strong><i class="bi bi-exclamation-triangle"></i> Staff is fully booked on this day!</strong>`;
                }
            }

            // Build options
            const options = periods.map(p => {
                let status = '';
                let isDisabled = false;
                let statusClass = '';

                if (sectionBusyPeriods.includes(p.period_number)) {
                    status = '(Section Busy)';
                    isDisabled = true;
                    statusClass = 'text-danger';
                } else if (staffBusyPeriods.includes(p.period_number)) {
                    status = '(Staff Busy)';
                    isDisabled = true;
                    statusClass = 'text-warning';
                } else {
                    status = '(Available)';
                    statusClass = 'text-success';
                }

                return `<option value="${p.period_number}" ${isDisabled ? 'disabled' : ''} class="${statusClass}">
                        Period ${p.period_number} (${p.start_time} - ${p.end_time}) ${status}
                    </option>`;
            }).join('');

            periodSelect.innerHTML += options;
        })
        .catch(err => {
            console.error('Error refreshing periods:', err);
            periodSelect.innerHTML = '<option value="">Error loading periods</option>';
        });
}

function fetchNextPeriodNumber() {
    const levelId = document.getElementById('periodGrade').value;
    const sectionId = document.getElementById('periodSection').value;

    if (!levelId || !sectionId) {
        document.getElementById('periodNumber').value = '';
        return;
    }

    fetch(`/api/timetable/next-period-number?level_id=${levelId}&section_id=${sectionId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('periodNumber').value = data.next_period_number;
            }
        });
}

let duplicateCheckTimer = null;
function checkDuplicatePeriodName() {
    if (duplicateCheckTimer) clearTimeout(duplicateCheckTimer);

    duplicateCheckTimer = setTimeout(() => {
        const name = document.getElementById('periodName').value;
        const levelId = document.getElementById('periodGrade').value;
        const sectionId = document.getElementById('periodSection').value;

        if (name.length < 2) {
            document.getElementById('duplicateAlert').classList.add('d-none');
            document.getElementById('quickFillContainer').classList.add('d-none');
            return;
        }

        // Check duplicates
        fetch(`/api/timetable/period/check-duplicate?level_id=${levelId}&section_id=${sectionId}&period_name=${encodeURIComponent(name)}`)
            .then(r => r.json())
            .then(data => {
                const alert = document.getElementById('duplicateAlert');
                if (data.success && data.is_duplicate) {
                    alert.classList.remove('d-none');
                    alert.dataset.existingPeriod = JSON.stringify(data.period);
                } else {
                    alert.classList.add('d-none');
                    fetchSimilarPeriods(name);
                }
            });
    }, 500);
}

function fetchSimilarPeriods(name) {
    fetch(`/api/timetable/similar-periods?period_name=${encodeURIComponent(name)}`)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('quickFillContainer');
            const chips = document.getElementById('suggestionChips');

            if (data.success && data.suggestions.length > 0) {
                container.classList.remove('d-none');
                chips.innerHTML = data.suggestions.map(s => `
                    <div class="suggestion-chip" onclick="applySuggestion('${s.start_time}', '${s.end_time}')" 
                         style="cursor: pointer; background: #e9ecef; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">
                        <i class="bi bi-magic"></i> ${s.start_time}-${s.end_time} (${s.source})
                    </div>
                `).join('');
            } else {
                container.classList.add('d-none');
            }
        });
}

function applySuggestion(start, end) {
    document.getElementById('startTime').value = start;
    document.getElementById('endTime').value = end;
    showAlert('Timings applied from suggestion', 'success');
}

function cloneExistingPeriod() {
    const alert = document.getElementById('duplicateAlert');
    const existing = JSON.parse(alert.dataset.existingPeriod);

    document.getElementById('startTime').value = existing.start_time;
    document.getElementById('endTime').value = existing.end_time;
    alert.classList.add('d-none');
    showAlert('Timings cloned from existing period', 'success');
}

function editExistingPeriod() {
    const alert = document.getElementById('duplicateAlert');
    const existing = JSON.parse(alert.dataset.existingPeriod);

    document.getElementById('periodModal').dataset.editId = existing.id;
    document.getElementById('periodNumber').value = existing.period_number;
    document.getElementById('startTime').value = existing.start_time;
    document.getElementById('endTime').value = existing.end_time;
    document.getElementById('periodModalTitle').textContent = 'Edit Period';

    alert.classList.add('d-none');
    showAlert('Now editing the existing period', 'info');
}

function deletePeriod(periodId) {
    if (!confirm('Are you sure you want to delete this period?')) return;

    fetch('/api/timetable/period/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({ school_id: schoolId, period_id: periodId })
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Period deleted successfully', 'success');
                loadPeriods();
            } else {
                showAlert(result.error || 'Failed to delete period', 'error');
            }
        })
        .catch(err => console.error('Error deleting period:', err));
}

// ==========================================================================
// DEPARTMENT PERMISSIONS
// ==========================================================================

function loadDepartments() {
    console.log('Loading departments for school_id:', schoolId);
    fetch(`/api/timetable/departments?school_id=${schoolId}`)
        .then(r => {
            console.log('Departments API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Departments data received:', data);
            allDepartments = data.departments || [];
            console.log(`Loaded ${allDepartments.length} departments`);
            renderDepartmentsTable();
        })
        .catch(err => {
            console.error('Error loading departments:', err);
            showAlert('Failed to load departments: ' + err.message, 'warning');
        });
}

function renderDepartmentsTable() {
    const tbody = document.getElementById('departmentsTableBody');

    if (allDepartments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="padding: 2rem; text-align: center; color: white;">Loading departments...</td></tr>';
        return;
    }

    tbody.innerHTML = allDepartments.map(d => `
        <tr>
            <td style="padding: 1rem; font-weight: 600;">${d.department}</td>
            <td style="padding: 1rem; text-align: center;">
                <label class="custom-switch">
                    <input type="checkbox" ${d.allow_alterations ? 'checked' : ''} 
                        onchange="toggleDepartmentPermission('${d.department}', 'alterations', this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
            <td style="padding: 1rem; text-align: center;">
                <label class="custom-switch">
                    <input type="checkbox" ${d.allow_inbound ? 'checked' : ''} 
                        onchange="toggleDepartmentPermission('${d.department}', 'inbound', this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
            <td style="padding: 1rem; text-align: center;">
                <button class="btn btn-sm btn-outline-primary" onclick="saveDepartmentPermission('${d.department}')">
                    <i class="bi bi-check-circle"></i> Save
                </button>
            </td>
        </tr>
    `).join('');
}

function toggleDepartmentPermission(department, permType, value) {
    // Store in data attribute for later save
    const row = event.target.closest('tr');
    if (!row.dataset.permissions) row.dataset.permissions = JSON.stringify({});
    const perms = JSON.parse(row.dataset.permissions);
    if (permType === 'alterations') perms.allow_alterations = value;
    if (permType === 'inbound') perms.allow_inbound = value;
    row.dataset.permissions = JSON.stringify(perms);
}

function saveDepartmentPermission(department) {
    const row = event.target.closest('tr');
    const perms = JSON.parse(row.dataset.permissions || '{}');

    const data = {
        school_id: schoolId,
        department: department,
        allow_alterations: perms.allow_alterations !== false,
        allow_inbound: perms.allow_inbound !== false
    };

    fetch('/api/timetable/department/permission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Department permissions updated', 'success');
                loadDepartments();
            } else {
                showAlert(result.error || 'Failed to update permissions', 'error');
            }
        })
        .catch(err => console.error('Error saving permissions:', err));
}

// ==========================================================================
// STAFF ASSIGNMENTS & ADMIN OVERRIDE
// ==========================================================================

function loadStaffList() {
    console.log('Loading staff for school_id:', schoolId);
    fetch(`/api/staff/list?school_id=${schoolId}`)
        .then(r => {
            console.log('Staff API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Staff data received:', data);
            allStaff = data.staff || [];
            console.log(`Loaded ${allStaff.length} staff members`);
            populateStaffSelect();
        })
        .catch(err => {
            console.error('Error loading staff:', err);
            showAlert('Failed to load staff: ' + err.message, 'warning');
        });
}

function populateStaffSelect() {
    // Populate the main staff assignment dropdown
    const mainSelect = document.getElementById('staffSelectAssign');
    if (mainSelect) {
        mainSelect.innerHTML = '<option value="">-- Choose Staff Member --</option>' +
            allStaff.map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
        console.log(`✅ Populated staffSelectAssign with ${allStaff.length} staff`);
    }

    // Populate the admin override modal dropdown
    const overrideSelect = document.getElementById('overrideStaffSelect');
    if (overrideSelect) {
        overrideSelect.innerHTML = '<option>-- Choose staff member --</option>' +
            allStaff.map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
        console.log(`✅ Populated overrideStaffSelect with ${allStaff.length} staff`);
    }

    // Populate the staff filter dropdown in assignments summary
    const filterSelect = document.getElementById('staffAssignmentStaffFilter');
    if (filterSelect) {
        filterSelect.innerHTML = '<option value="">All Staff</option>' +
            allStaff.map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
    }
}

function loadDayAssignments() {
    const dayValue = document.getElementById('daySelector').value;
    if (!dayValue) {
        document.getElementById('assignmentsTableBody').innerHTML =
            '<tr><td colspan="7" style="padding: 2rem; text-align: center;">Select a day to view</td></tr>';
        return;
    }

    // Use hierarchical API
    fetch(`/api/hierarchical-timetable/assignments/all?day_of_week=${dayValue}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load assignments: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.data) {
                currentAssignments = data.data;
            } else {
                currentAssignments = [];
            }
            renderAssignmentsTable();
        })
        .catch(err => {
            console.error('Error loading assignments:', err);
            showAlert('Failed to load assignments: ' + err.message, 'error');
        });
}

function renderAssignmentsTable() {
    const tbody = document.getElementById('assignmentsTableBody');

    if (currentAssignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="padding: 2rem; text-align: center; color: white;">No assignments for this day</td></tr>';
        return;
    }

    tbody.innerHTML = currentAssignments.map(a => `
        <tr>
            <td style="padding: 1rem;">
                <div class="fw-bold text-white">${a.full_name}</div>
                <small class="opacity-75">${a.department}</small>
            </td>
            <td style="padding: 1rem;">
                <span class="badge bg-light text-dark border">${a.level_name} - ${a.section_name}</span>
            </td>
            <td style="padding: 1rem;">
                 <div class="text-white">${a.subject_name || '-'}</div>
                 <small class="opacity-75">Period ${a.period_number}</small>
            </td>
            <td style="padding: 1rem; font-family: monospace;">${a.start_time} - ${a.end_time}</td>
            <td style="padding: 1rem;">${a.room_number || '-'}</td>
            <td style="padding: 1rem;">
                ${a.is_locked
            ? '<span class="status-badge status-locked"><i class="bi bi-lock"></i> Locked</span>'
            : '<span class="status-badge status-active">Active</span>'
        }
            </td>
            <td style="padding: 1rem; text-align: center;">
                <button class="btn btn-sm btn-override" onclick="showOverrideModal(${a.id})">
                    <i class="bi bi-shield-check"></i> Override
                </button>
            </td>
        </tr>
    `).join('');
}

function filterAssignments() {
    const search = document.getElementById('staffSearchInput').value.toLowerCase();
    const rows = document.getElementById('assignmentsTableBody').querySelectorAll('tr');

    rows.forEach(row => {
        const staffName = row.cells[0]?.textContent.toLowerCase() || '';
        row.style.display = staffName.includes(search) ? '' : 'none';
    });
}

function showOverrideModal(assignmentId) {
    document.getElementById('overrideModal').dataset.assignmentId = assignmentId;
    document.getElementById('overrideStaffSelect').value = '';
    document.getElementById('overrideNotes').value = '';
    new bootstrap.Modal(document.getElementById('overrideModal')).show();
}

function performAdminOverride() {
    const assignmentId = document.getElementById('overrideModal').dataset.assignmentId;
    const newStaffId = document.getElementById('overrideStaffSelect').value;
    const notes = document.getElementById('overrideNotes').value;

    if (!newStaffId) {
        showAlert('Please select a staff member', 'error');
        return;
    }

    const data = {
        school_id: schoolId,
        assignment_id: assignmentId,
        new_staff_id: newStaffId,
        admin_notes: notes
    };

    fetch('/api/timetable/assignment/override', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Assignment reassigned successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('overrideModal')).hide();
                loadDayAssignments();
            } else {
                showAlert(result.error || 'Failed to override assignment', 'error');
            }
        })
        .catch(err => {
            console.error('Error overriding assignment:', err);
            showAlert('Error overriding assignment', 'error');
        });
}

// ==========================================================================
// UTILITY FUNCTIONS
// ==========================================================================

function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info';
    const iconClass = type === 'error' ? 'bi-exclamation-circle' : type === 'success' ? 'bi-check-circle' : 'bi-info-circle';

    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="bi ${iconClass}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', alertHTML);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}

function refreshData() {
    loadPeriods();
    loadDepartments();
    if (document.getElementById('daySelector').value) {
        loadDayAssignments();
    }
    showAlert('Data refreshed', 'success');
}

function saveAllSettings() {
    showAlert('All settings saved successfully', 'success');
}

// ============================================================================
// ENHANCED STAFF PERIOD ALLOCATION FUNCTIONS
// ============================================================================

/**
 * Called when a staff member is selected
 * Shows the allocation interface and loads their current allocations
 */
/**
 * Called when a staff member is selected
 * Shows the allocation interface and loads their current allocations
 */
function onStaffSelected() {
    const staffSelect = document.getElementById('staffSelectAssign');
    const staffId = staffSelect.value;
    const staffName = staffSelect.options[staffSelect.selectedIndex].text;

    const allocationSection = document.getElementById('allocationSection');
    const currentAllocationsSection = document.getElementById('currentAllocationsSection');
    const staffInfoDisplay = document.getElementById('staffInfoDisplay');
    const staffInfoText = document.getElementById('staffInfoText');
    const divider = document.getElementById('staffPeriodsDivider');

    if (!staffId) {
        // Hide sections if no staff selected
        allocationSection.style.display = 'none';
        currentAllocationsSection.style.display = 'none';
        staffInfoDisplay.classList.add('d-none');
        divider.style.display = 'none';
        return;
    }

    // Show allocation interface
    allocationSection.style.display = 'block';
    divider.style.display = 'block';

    // Show staff info
    staffInfoDisplay.classList.remove('d-none');
    staffInfoText.textContent = `Currently managing allocations for: ${staffName}`;

    // Populate Grade selection for assignment
    populateAssignGrades();

    // Load current allocations for this staff
    loadStaffCurrentAllocations(staffId);
}

function populateAssignGrades() {
    const gradeSelect = document.getElementById('gradeSelectAssign');
    if (!gradeSelect) return;

    gradeSelect.innerHTML = '<option value="">-- Choose Grade --</option>';
    allLevels.forEach(level => {
        gradeSelect.innerHTML += `<option value="${level.id}">${level.level_name}</option>`;
    });
}

function onAssignGradeChange() {
    const levelId = document.getElementById('gradeSelectAssign').value;
    const sectionSelect = document.getElementById('sectionSelectAssign');
    const periodSelect = document.getElementById('periodSelectAssign');

    sectionSelect.innerHTML = '<option value="">-- Choose Section --</option>';
    periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';

    if (levelId) {
        const filtered = allSections.filter(s => s.level_id == levelId);
        sectionSelect.innerHTML += filtered.map(s => `<option value="${s.id}">${s.section_name}</option>`).join('');
    }
}

function onAssignSectionChange() {
    const levelId = document.getElementById('gradeSelectAssign').value;
    const sectionId = document.getElementById('sectionSelectAssign').value;
    const periodSelect = document.getElementById('periodSelectAssign');

    periodSelect.innerHTML = '<option value="">-- Loading... --</option>';

    if (!levelId || !sectionId) {
        periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';
        return;
    }

    // Fetch periods for this specific section
    fetch(`/api/timetable/periods?school_id=${schoolId}&level_id=${levelId}&section_id=${sectionId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.periods) {
                periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';
                data.periods.forEach(p => {
                    periodSelect.innerHTML += `<option value="${p.period_number}" data-id="${p.id}">${p.period_name || `Period ${p.period_number}`} (${p.start_time}-${p.end_time})</option>`;
                });
            } else {
                periodSelect.innerHTML = '<option value="">No periods defined for this section</option>';
            }
        })
        .catch(err => {
            console.error('Error loading periods for assignment:', err);
            periodSelect.innerHTML = '<option value="">Error loading periods</option>';
        });
}

/**
 * Load current period allocations for a specific staff member
 */
function loadStaffCurrentAllocations(staffId) {
    const tbody = document.getElementById('staffCurrentAllocationsBody');
    const section = document.getElementById('currentAllocationsSection');

    // Use hierarchical API
    fetch(`/api/hierarchical-timetable/staff-schedule/${staffId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load allocations');
            return response.json();
        })
        .then(data => {
            if (data.success && data.data && data.data.schedule && data.data.schedule.length > 0) {
                const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

                tbody.innerHTML = data.data.schedule.map(allocation => {
                    const day = DAYS[allocation.day_of_week] || 'Unknown';
                    const periodName = `Period ${allocation.period_number}`;
                    const timeSlot = `${allocation.start_time} to ${allocation.end_time}`;
                    const subject = allocation.subject_name || 'No Subject';
                    const location = allocation.room_number ? `<br><small class="text-muted"><i class="bi bi-geo-alt"></i> ${allocation.room_number}</small>` : '';

                    return `
                        <tr>
                            <td><strong>${day}</strong></td>
                            <td>
                                <div>${allocation.level_name} - ${allocation.section_name}</div>
                                <small class="text-primary fw-600">${periodName}</small>
                            </td>
                            <td>
                                <div class="fw-bold">${subject}</div>
                                <code>${timeSlot}</code>
                                ${location}
                            </td>
                            <td><span class="badge ${allocation.is_locked ? 'bg-danger' : 'bg-success'}">${allocation.is_locked ? 'Locked' : 'Active'}</span></td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-outline-primary me-1" onclick="editStaffAllocation(${allocation.assignment_id}, ${staffId}, '${subject.replace(/'/g, "\\'")}', '${allocation.room_number || ''}')" title="Edit Assignment">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteStaffAllocation(${allocation.assignment_id}, ${staffId})" title="Delete Assignment">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');

                section.style.display = 'block';
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-muted py-5">
                            <div class="mb-2"><i class="bi bi-inbox fs-2 opacity-25"></i></div>
                            No periods allocated yet. Add one above!
                        </td>
                    </tr>
                `;
                section.style.display = 'block';
            }
        })
        .catch(err => {
            console.error('Error loading allocations:', err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-danger py-3">
                        <i class="bi bi-exclamation-circle"></i> Error loading allocations
                    </td>
                </tr>
            `;
            section.style.display = 'block';
        });
}

/**
 * Assign a period to a staff member
 */
function assignStaffPeriod() {
    const staffSelect = document.getElementById('staffSelectAssign');
    const daySelect = document.getElementById('daySelectAssign');
    const gradeSelect = document.getElementById('gradeSelectAssign');
    const sectionSelect = document.getElementById('sectionSelectAssign');
    const periodSelect = document.getElementById('periodSelectAssign');
    const subjectInput = document.getElementById('subjectNameAssign');
    const roomInput = document.getElementById('roomNumberAssign');

    const staffId = staffSelect.value;
    const day = daySelect.value;
    const levelId = gradeSelect.value;
    const sectionId = sectionSelect.value;
    const periodNumber = periodSelect.value;

    // Validation
    if (!staffId || !day || !levelId || !sectionId || !periodNumber) {
        showAlert('Please fill all required fields: Staff, Day, Grade, Section, and Period', 'error');
        return;
    }

    const data = {
        staff_id: parseInt(staffId),
        day_of_week: parseInt(day),
        level_id: parseInt(levelId),
        section_id: parseInt(sectionId),
        period_number: parseInt(periodNumber),
        subject_name: subjectInput.value,
        room_number: roomInput.value
    };

    console.log('Sending assignment data:', data);

    // Make API call to assign period using hierarchical API
    fetch('/api/hierarchical-timetable/assign-staff', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Successfully assigned staff to the selected period`, 'success');

                // Reset inputs but keep staff/day for convenience
                periodSelect.value = '';
                subjectInput.value = '';
                roomInput.value = '';

                // Reload allocations
                loadStaffCurrentAllocations(staffId);

                // Refresh the summary table as well
                loadStaffAssignmentsSummary();
            } else {
                let errorMsg = data.error || 'Failed to allocate period';
                if (data.conflicts && data.conflicts.length > 0) {
                    errorMsg += `\nConflicts with: ${data.conflicts.join(', ')}`;
                }
                showAlert(`Error: ${errorMsg}`, 'error');
            }
        })
        .catch(err => {
            console.error('Error assigning period:', err);
            showAlert('Error assigning period. Please check network/auth.', 'error');
        });
}

/**
 * Delete a period allocation for a staff member
 */
function deleteStaffAllocation(assignmentId, staffId) {
    if (!confirm('Are you sure you want to remove this assignment?')) {
        return;
    }

    fetch(`/api/hierarchical-timetable/assignment/${assignmentId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Assignment removed successfully', 'success');
                loadStaffCurrentAllocations(staffId);

                // Refresh the summary table as well
                loadStaffAssignmentsSummary();
            } else {
                showAlert(`Error: ${data.error || 'Failed to delete assignment'}`, 'error');
            }
        })
        .catch(err => {
            console.error('Error deleting assignment:', err);
            showAlert('Error deleting assignment. Please try again.', 'error');
        });
}

/**
 * Edit a period allocation for a staff member
 */
function editStaffAllocation(assignmentId, staffId, currentSubject, currentRoom) {
    // Get the modal
    const modal = document.getElementById('editAllocationModal');
    if (!modal) {
        console.error('Edit modal not found');
        return;
    }

    // Populate the form
    document.getElementById('editAssignmentId').value = assignmentId;
    document.getElementById('editStaffId').value = staffId;
    document.getElementById('editSubjectName').value = currentSubject;
    document.getElementById('editRoomNumber').value = currentRoom;

    // Show the modal
    const editModal = new bootstrap.Modal(modal);
    editModal.show();
}

/**
 * Save edited allocation
 */
function saveEditedAllocation() {
    const assignmentId = document.getElementById('editAssignmentId').value;
    const staffId = document.getElementById('editStaffId').value;
    const subjectName = document.getElementById('editSubjectName').value;
    const roomNumber = document.getElementById('editRoomNumber').value;

    if (!assignmentId || !staffId) {
        showAlert('Missing assignment or staff information', 'error');
        return;
    }

    // Show loading state
    const saveBtn = document.getElementById('saveEditedAllocationBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

    // Make API call to update
    fetch(`/api/hierarchical-timetable/assignment/${assignmentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            subject_name: subjectName,
            room_number: roomNumber
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Assignment updated successfully', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editAllocationModal'));
                if (modal) {
                    modal.hide();
                }

                // Reload allocations
                loadStaffCurrentAllocations(staffId);

                // Refresh the summary table as well
                loadStaffAssignmentsSummary();
            } else {
                showAlert(`Error: ${data.error || 'Failed to update assignment'}`, 'error');
            }
        })
        .catch(err => {
            console.error('Error updating assignment:', err);
            showAlert('Error updating assignment. Please try again.', 'error');
        })
        .finally(() => {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        });
}

/**
 * Get all allocations and display as calendar grid for a staff member
 */
function loadStaffAllocationScheduleGrid(staffId) {
    fetch(`/api/timetable/staff-period/list/${staffId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                generateAllocationScheduleGrid(data.data);
            }
        })
        .catch(err => console.error('Error loading schedule grid:', err));
}

/**
 * Generate visual schedule grid for staff allocations
 */
function generateAllocationScheduleGrid(allocations) {
    const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const PERIODS = {};

    // Build period map
    allPeriods.forEach(period => {
        PERIODS[period.id] = `${period.period_name || `Period ${period.period_number}`}`;
    });

    // Create grid structure
    let gridHTML = '<div class="allocation-schedule-grid">';

    DAYS.forEach((day, dayIdx) => {
        gridHTML += `
            <div class="allocation-day-column">
                <div class="day-header">${day}</div>
        `;

        allocations
            .filter(a => a.day_of_week === dayIdx)
            .forEach(alloc => {
                const period = PERIODS[alloc.period_id] || `Period ${alloc.period_id}`;
                gridHTML += `
                    <div class="period-slot allocated">
                        <span>${period}</span>
                        <small>${alloc.time_slot}</small>
                    </div>
                `;
            });

        gridHTML += '</div>';
    });

    gridHTML += '</div>';

    return gridHTML;
}

// ===================================
// STAFF ASSIGNMENTS SUMMARY & AVAILABILITY
// ===================================

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function getDayName(idx) {
    return dayNames[idx] || 'Unknown';
}

function loadStaffAssignmentsSummary() {
    const dayFilter = document.getElementById('staffAssignmentDayFilter')?.value || '';
    const tbody = document.getElementById('staffAssignmentsTableBody');

    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5" class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted">Loading staff availability...</div></td></tr>';

    let url = `/api/hierarchical-timetable/assignments/availability`;
    if (dayFilter !== "") {
        url += `?day_of_week=${dayFilter}`;
    }

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.data) {
                renderStaffAssignmentsSummary(data.data);
            } else {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading data: ${data.error || 'Unknown error'}</td></tr>`;
            }
        })
        .catch(err => {
            console.error('Error:', err);
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading data. Please try again.</td></tr>`;
        });
}

function renderStaffAssignmentsSummary(data) {
    const tbody = document.getElementById('staffAssignmentsTableBody');
    tbody.innerHTML = '';

    // Filter by staff if selected
    const staffFilterId = document.getElementById('staffAssignmentStaffFilter')?.value;
    let filteredData = data;
    if (staffFilterId) {
        filteredData = data.filter(item => item.staff_id == staffFilterId);
    }

    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center p-4 text-muted"><i class="bi bi-inbox me-2"></i>No data found for the selected criteria.</td></tr>';
        return;
    }

    filteredData.forEach(item => {
        const assignedBadges = item.assigned_periods.length > 0
            ? item.assigned_periods.map(p => `<span class="badge bg-primary me-1">${p}</span>`).join('')
            : '<span class="text-muted small">None</span>';

        const freeBadges = item.free_periods.length > 0
            ? item.free_periods.map(p => `<span class="badge bg-success me-1">${p}</span>`).join('')
            : '<span class="badge bg-danger">Fully Booked</span>';

        // Status logic
        let statusBadge = '<span class="badge bg-success">Available</span>';
        if (item.free_periods.length === 0) statusBadge = '<span class="badge bg-danger">Full</span>';
        else if (item.assigned_periods.length === 0) statusBadge = '<span class="badge bg-secondary">Free</span>';

        const row = `
            <tr>
                <td>
                    <div class="fw-bold">${item.staff_name}</div>
                    <small class="text-muted">${item.department || ''}</small>
                </td>
                <td>${getDayName(item.day)}</td>
                <td>${assignedBadges}</td>
                <td>${freeBadges}</td>
                <td class="text-center">${statusBadge}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}
