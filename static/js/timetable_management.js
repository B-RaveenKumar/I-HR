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
let allPeriodTimings = [];
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
    loadPeriodTimings();
    loadPeriods();
    loadDepartments();
    loadStaffList();
    loadStaffAssignmentsSummary();
    initPeriodTimingBulkUpload();
    initPeriodBulkUpload();
    initStaffPeriodBulkUpload();
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
        tbody.innerHTML = '<tr style="background: #f8f9fa;"><td colspan="6" style="padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No periods defined. Add one to get started!</td></tr>';
        return;
    }

    tbody.innerHTML = allPeriods.map(p => {
        const level = allLevels.find(l => l.id == p.level_id);
        const section = allSections.find(s => s.id == p.section_id);
        const gsLabel = level ? `${level.level_name} - ${section ? section.section_name : 'All'}` : 'Global';
        const subjectName = p.period_name || '-';
        const slotName = p.slot_label && p.slot_label !== p.period_name ? p.slot_label : '';

        const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const dayLabel = p.day_of_week !== null && p.day_of_week !== undefined ? DAYS[p.day_of_week] : 'All Days';

        return `
            <tr>
                <td style="padding: 1rem;">
                    <div>${gsLabel}</div>
                    <small class="text-muted"><i class="bi bi-calendar2-week"></i> ${dayLabel}</small>
                </td>
                <td style="padding: 1rem;">
                    <span>${subjectName}</span>
                    ${slotName ? `<small class="text-muted ms-2">(${slotName})</small>` : ''}
                </td>
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

function loadPeriodTimings() {
    fetch(`/api/timetable/period-timings?school_id=${schoolId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.error || 'Failed to load period timings');
            }
            allPeriodTimings = data.timings || [];
            renderPeriodTimingsTable();
            populatePeriodTimeSlotDropdown();
        })
        .catch(err => {
            console.error('Error loading period timings:', err);
            showAlert('Failed to load period timings: ' + err.message, 'error');
        });
}

function renderPeriodTimingsTable() {
    const tbody = document.getElementById('periodTimingsTableBody');
    if (!tbody) return;

    if (allPeriodTimings.length === 0) {
        tbody.innerHTML = '<tr style="background: #f8f9fa;"><td colspan="6" style="padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No time slots defined yet.</td></tr>';
        return;
    }

    tbody.innerHTML = allPeriodTimings.map(t => `
        <tr>
            <td style="padding: 1rem;"><span class="duration-badge">P${t.period_sequence || '-'}</span></td>
            <td style="padding: 1rem; font-weight: 600;">${t.slot_label}</td>
            <td style="padding: 1rem;"><span class="time-display">${t.start_time}</span></td>
            <td style="padding: 1rem;"><span class="time-display">${t.end_time}</span></td>
            <td style="padding: 1rem;"><span class="duration-badge">${t.duration_minutes} mins</span></td>
            <td style="padding: 1rem; text-align: center;">
                <div class="action-buttons">
                    <button class="btn-edit btn-sm" onclick="editPeriodTiming(${t.id})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn-delete-action btn-sm" onclick="deletePeriodTiming(${t.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function populatePeriodTimeSlotDropdown(selectedId = '') {
    const dropdown = document.getElementById('periodTimeSlot');
    if (!dropdown) return;

    dropdown.innerHTML = '<option value="">-- Select Time Slot --</option>';
    dropdown.innerHTML += allPeriodTimings.map(t =>
        `<option value="${t.id}">Period ${t.period_sequence || '?'} - ${t.slot_label} (${t.start_time} - ${t.end_time})</option>`
    ).join('');

    if (selectedId) {
        dropdown.value = String(selectedId);
    }
}

function getMeridiemFromTime(timeValue) {
    if (!timeValue || !timeValue.includes(':')) {
        return 'AM';
    }

    const [hourStr] = timeValue.split(':');
    const hour = parseInt(hourStr, 10);
    return hour >= 12 ? 'PM' : 'AM';
}

function syncTimingMeridiem(timeInputId, meridiemSelectId) {
    const timeInput = document.getElementById(timeInputId);
    const meridiemSelect = document.getElementById(meridiemSelectId);
    if (!timeInput || !meridiemSelect || !timeInput.value) return;

    meridiemSelect.value = getMeridiemFromTime(timeInput.value);
}

function to24HourTime(timeValue, meridiem) {
    if (!timeValue || !timeValue.includes(':')) {
        return timeValue;
    }

    const [hourStr, minuteStr] = timeValue.split(':');
    const rawHour = parseInt(hourStr, 10);
    const baseHour = rawHour % 12;
    const hour24 = meridiem === 'PM' ? baseHour + 12 : baseHour;

    return `${String(hour24).padStart(2, '0')}:${minuteStr}`;
}

function showAddTimingModal() {
    document.getElementById('timingLabel').value = '';
    document.getElementById('timingSequence').value = '';
    document.getElementById('timingStart').value = '';
    document.getElementById('timingEnd').value = '';
    document.getElementById('timingStartMeridiem').value = 'AM';
    document.getElementById('timingEndMeridiem').value = 'AM';
    document.getElementById('periodTimingModalTitle').textContent = 'Add Time Slot';
    document.getElementById('periodTimingModal').dataset.editId = '';

    new bootstrap.Modal(document.getElementById('periodTimingModal')).show();
}

function editPeriodTiming(timingId) {
    const timing = allPeriodTimings.find(t => t.id === timingId);
    if (!timing) return;

    document.getElementById('timingLabel').value = timing.slot_label || '';
    document.getElementById('timingSequence').value = timing.period_sequence || '';
    document.getElementById('timingStart').value = timing.start_time || '';
    document.getElementById('timingEnd').value = timing.end_time || '';
    document.getElementById('timingStartMeridiem').value = getMeridiemFromTime(timing.start_time || '');
    document.getElementById('timingEndMeridiem').value = getMeridiemFromTime(timing.end_time || '');
    document.getElementById('periodTimingModalTitle').textContent = 'Edit Time Slot';
    document.getElementById('periodTimingModal').dataset.editId = timingId;

    new bootstrap.Modal(document.getElementById('periodTimingModal')).show();
}

function savePeriodTiming() {
    const slotLabel = document.getElementById('timingLabel').value.trim();
    const periodSequence = parseInt(document.getElementById('timingSequence').value, 10);
    const startTime = document.getElementById('timingStart').value;
    const endTime = document.getElementById('timingEnd').value;
    const startMeridiem = document.getElementById('timingStartMeridiem').value;
    const endMeridiem = document.getElementById('timingEndMeridiem').value;
    const editId = document.getElementById('periodTimingModal').dataset.editId;

    if (!slotLabel || !Number.isInteger(periodSequence) || periodSequence <= 0 || !startTime || !endTime) {
        showAlert('Please fill all required fields', 'error');
        return;
    }

    const normalizedStartTime = to24HourTime(startTime, startMeridiem);
    const normalizedEndTime = to24HourTime(endTime, endMeridiem);

    const payload = {
        school_id: schoolId,
        slot_label: slotLabel,
        period_sequence: periodSequence,
        start_time: normalizedStartTime,
        end_time: normalizedEndTime
    };

    if (editId) {
        payload.id = parseInt(editId);
    }

    fetch('/api/timetable/period-timing/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(payload)
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Time slot saved successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('periodTimingModal'));
                if (modal) modal.hide();
                loadPeriodTimings();
                loadPeriods();
                refreshAssignablePeriods();
            } else {
                showAlert(result.error || 'Failed to save time slot', 'error');
            }
        })
        .catch(err => showAlert('Error saving time slot: ' + err.message, 'error'));
}

function deletePeriodTiming(timingId) {
    if (!confirm('Are you sure you want to delete this time slot?')) return;

    fetch('/api/timetable/period-timing/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({ school_id: schoolId, timing_id: timingId })
    })
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                showAlert('Time slot deleted successfully', 'success');
                loadPeriodTimings();
            } else {
                showAlert(result.error || 'Failed to delete time slot', 'error');
            }
        })
        .catch(err => showAlert('Error deleting time slot: ' + err.message, 'error'));
}

function downloadPeriodTimingTemplate() {
    window.location.href = '/api/timetable/period-timings/template';
}

function initPeriodTimingBulkUpload() {
    const form = document.getElementById('bulkUploadPeriodTimingForm');
    if (!form) return;

    form.addEventListener('submit', handlePeriodTimingBulkUpload);

    const modalEl = document.getElementById('bulkUploadPeriodTimingModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', () => {
            const resultBox = document.getElementById('bulkPeriodTimingUploadResult');
            if (resultBox) {
                resultBox.className = 'd-none';
                resultBox.innerHTML = '';
            }
            form.reset();
        });
    }
}

function handlePeriodTimingBulkUpload(e) {
    e.preventDefault();

    const form = e.target;
    const fileInput = document.getElementById('bulkPeriodTimingFile');
    const submitBtn = document.getElementById('bulkPeriodTimingUploadSubmitBtn');
    const resultBox = document.getElementById('bulkPeriodTimingUploadResult');

    if (!fileInput || !fileInput.files || !fileInput.files.length) {
        showAlert('Please select an Excel/CSV file to upload.', 'error');
        return;
    }

    const formData = new FormData(form);
    formData.append('school_id', schoolId);

    const originalBtnHtml = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';

    resultBox.className = 'd-none';
    resultBox.innerHTML = '';

    fetch('/api/timetable/period-timings/bulk-upload', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                resultBox.className = 'alert alert-danger';
                resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${data.error || 'Bulk upload failed'}`;
                resultBox.classList.remove('d-none');
                return;
            }

            const importedCount = data.imported_count || 0;
            const totalRows = data.total_rows || 0;
            const failedCount = Math.max((data.failed_count ?? (totalRows - importedCount)), 0);
            const errors = Array.isArray(data.errors) ? data.errors : [];

            let errorsHtml = '';
            if (errors.length) {
                const topErrors = errors.slice(0, 10).map(err => `<li>${err}</li>`).join('');
                const moreErrors = errors.length > 10 ? `<li>...and ${errors.length - 10} more error(s)</li>` : '';
                errorsHtml = `
                    <hr>
                    <div class="mb-1"><strong>Import issues:</strong></div>
                    <ul class="mb-0">${topErrors}${moreErrors}</ul>
                `;
            }

            resultBox.className = errors.length ? 'alert alert-warning' : 'alert alert-success';
            resultBox.innerHTML = `
                <div><strong>Bulk upload completed.</strong></div>
                <div>Imported: ${importedCount} | Failed: ${failedCount} | Total rows: ${totalRows}</div>
                ${errorsHtml}
            `;
            resultBox.classList.remove('d-none');

            if (importedCount > 0) {
                showAlert(`Bulk upload complete: ${importedCount} time slot(s) imported.`, 'success');
                loadPeriodTimings();
                loadPeriods();
            } else {
                showAlert('No time slots were imported. Check the file and try again.', 'error');
            }
        })
        .catch(err => {
            resultBox.className = 'alert alert-danger';
            resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Upload failed: ${err.message}`;
            resultBox.classList.remove('d-none');
            showAlert('Bulk upload failed. Please try again.', 'error');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        });
}

function showAddPeriodModal() {
    if (allPeriodTimings.length === 0) {
        loadPeriodTimings();
    }

    document.getElementById('periodGrade').value = '';
    document.getElementById('periodSection').innerHTML = '<option value="">-- Select Section --</option>';
    document.getElementById('periodDay').value = '';
    document.getElementById('periodSubjectName').value = '';
    populatePeriodTimeSlotDropdown();
    document.getElementById('periodTimeSlot').value = '';
    document.getElementById('periodModalTitle').textContent = 'Add Period';
    document.getElementById('periodModal').dataset.editId = '';
    delete document.getElementById('periodModal').dataset.periodNumber;

    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function editPeriod(periodId) {
    const period = allPeriods.find(p => p.id === periodId);
    if (!period) return;

    if (allPeriodTimings.length === 0) {
        loadPeriodTimings();
    }

    document.getElementById('periodGrade').value = period.level_id || '';
    onPeriodGradeChange(period.section_id);

    document.getElementById('periodDay').value = period.day_of_week === null || period.day_of_week === undefined ? '' : period.day_of_week;
    document.getElementById('periodSubjectName').value = period.period_name || '';
    populatePeriodTimeSlotDropdown(period.time_slot_id);

    if (!period.time_slot_id) {
        const fallbackTiming = allPeriodTimings.find(t => t.start_time === period.start_time && t.end_time === period.end_time);
        if (fallbackTiming) {
            document.getElementById('periodTimeSlot').value = String(fallbackTiming.id);
        }
    }

    document.getElementById('periodModalTitle').textContent = 'Edit Period';
    document.getElementById('periodModal').dataset.editId = periodId;
    document.getElementById('periodModal').dataset.periodNumber = period.period_number;

    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function savePeriod() {
    const levelId = document.getElementById('periodGrade').value;
    const sectionId = document.getElementById('periodSection').value;
    const dayOfWeek = document.getElementById('periodDay').value;
    const subjectName = document.getElementById('periodSubjectName').value.trim();
    const periodNumber = document.getElementById('periodModal').dataset.periodNumber;
    const timeSlotId = document.getElementById('periodTimeSlot').value;
    const editId = document.getElementById('periodModal').dataset.editId;

    if (!timeSlotId) {
        showAlert('Please fill all required fields', 'error');
        return;
    }

    const data = {
        school_id: schoolId,
        level_id: levelId || null,
        section_id: sectionId || null,
        day_of_week: dayOfWeek === '' ? null : parseInt(dayOfWeek),
        period_name: subjectName,
        time_slot_id: parseInt(timeSlotId)
    };

    if (periodNumber) {
        data.period_number = parseInt(periodNumber);
    }

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
                delete document.getElementById('periodModal').dataset.periodNumber;
                loadPeriods();
            } else {
                showAlert(result.error || 'Failed to save period', 'error');
            }
        })
        .catch(err => showAlert('Error saving period: ' + err.message, 'error'));
}

function downloadPeriodTemplate() {
    window.location.href = '/api/timetable/periods/template?school_id=' + schoolId;
}

function initPeriodBulkUpload() {
    const form = document.getElementById('bulkUploadPeriodForm');
    if (!form) return;

    form.addEventListener('submit', handlePeriodBulkUpload);

    const modalEl = document.getElementById('bulkUploadPeriodModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', () => {
            const resultBox = document.getElementById('bulkPeriodUploadResult');
            if (resultBox) {
                resultBox.className = 'd-none';
                resultBox.innerHTML = '';
            }
            form.reset();
        });
    }
}

function handlePeriodBulkUpload(e) {
    e.preventDefault();

    const form = e.target;
    const fileInput = document.getElementById('bulkPeriodFile');
    const submitBtn = document.getElementById('bulkPeriodUploadSubmitBtn');
    const resultBox = document.getElementById('bulkPeriodUploadResult');

    if (!fileInput || !fileInput.files || !fileInput.files.length) {
        showAlert('Please select an Excel/CSV file to upload.', 'error');
        return;
    }

    const formData = new FormData(form);
    formData.append('school_id', schoolId);

    const originalBtnHtml = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';

    resultBox.className = 'd-none';
    resultBox.innerHTML = '';

    fetch('/api/timetable/periods/bulk-upload', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                resultBox.className = 'alert alert-danger';
                resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${data.error || 'Bulk upload failed'}`;
                resultBox.classList.remove('d-none');
                return;
            }

            const importedCount = data.imported_count || 0;
            const totalRows = data.total_rows || 0;
            const failedCount = Math.max((data.failed_count ?? (totalRows - importedCount)), 0);
            const errors = Array.isArray(data.errors) ? data.errors : [];

            let errorsHtml = '';
            if (errors.length) {
                const topErrors = errors.slice(0, 10).map(err => `<li>${err}</li>`).join('');
                const moreErrors = errors.length > 10 ? `<li>...and ${errors.length - 10} more error(s)</li>` : '';
                errorsHtml = `
                    <hr>
                    <div class="mb-1"><strong>Import issues:</strong></div>
                    <ul class="mb-0">${topErrors}${moreErrors}</ul>
                `;
            }

            resultBox.className = errors.length ? 'alert alert-warning' : 'alert alert-success';
            resultBox.innerHTML = `
                <div><strong>Bulk upload completed.</strong></div>
                <div>Imported: ${importedCount} | Failed: ${failedCount} | Total rows: ${totalRows}</div>
                ${errorsHtml}
            `;
            resultBox.classList.remove('d-none');

            if (importedCount > 0) {
                showAlert(`Bulk upload complete: ${importedCount} period(s) imported.`, 'success');
                loadPeriods();
            } else {
                showAlert('No periods were imported. Check the file and try again.', 'error');
            }
        })
        .catch(err => {
            resultBox.className = 'alert alert-danger';
            resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Upload failed: ${err.message}`;
            resultBox.classList.remove('d-none');
            showAlert('Bulk upload failed. Please try again.', 'error');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        });
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

                // Refresh labels in periods table once levels are available
                renderPeriodsTable();

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

    const renderableLevels = allLevels.filter(level => Number.isInteger(Number.parseInt(level.id, 10)));

    if (renderableLevels.length === 0) {
        container.innerHTML = '<div class="p-4 text-center text-muted">No levels generated. Set Org Type first.</div>';
        return;
    }

    container.innerHTML = renderableLevels.map(level => {
        const levelId = Number.parseInt(level.id, 10);
        return `
        <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center level-item border-start-0 border-end-0" 
             style="cursor: pointer; padding: 1rem;" onclick="filterSectionsByLevel(${levelId}, this)">
            <div class="d-flex align-items-center flex-grow-1">
                <div class="me-3">
                   <span class="fw-600 d-block">${level.level_name}</span>
                   <small class="text-muted" style="font-size: 0.75rem;">${level.description || ''}</small>
                </div>
                <div class="d-flex align-items-center ms-auto me-2 gap-1">
                    <button class="btn btn-sm btn-outline-secondary border-0 opacity-50 hover-opacity-100"
                            onclick="event.stopPropagation(); editLevel(${levelId})" title="Edit Grade Name">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger border-0 opacity-50 hover-opacity-100"
                            onclick="event.stopPropagation(); deleteLevel(${levelId})" title="Delete Class">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <i class="bi bi-chevron-right text-muted small"></i>
        </div>
    `;
    }).join('');
}

function showAddLevelModal() {
    const form = document.getElementById('addLevelForm');
    if (form) form.reset();

    const modalEl = document.getElementById('addLevelModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    modal.show();
}

function createLevel() {
    const levelName = document.getElementById('newLevelName')?.value?.trim();
    const levelNumberRaw = document.getElementById('newLevelNumber')?.value;
    const description = document.getElementById('newLevelDescription')?.value?.trim() || '';

    if (!levelName) {
        showAlert('Class name is required', 'error');
        return;
    }

    const payload = {
        level_name: levelName,
        description: description
    };

    if (levelNumberRaw !== '') {
        payload.level_number = Number.parseInt(levelNumberRaw, 10);
    }

    fetch('/api/hierarchical-timetable/levels/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(payload)
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message || 'Class added successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addLevelModal'));
                if (modal) modal.hide();

                currentLevelFilter = data.level_id || currentLevelFilter;
                loadAcademicLevels();
                loadAllSections();
            } else {
                showAlert(data.error || 'Failed to create class', 'error');
            }
        })
        .catch(err => showAlert('Error creating class: ' + err.message, 'error'));
}

function deleteLevel(levelId) {
    const normalizedLevelId = Number.parseInt(levelId, 10);
    if (!Number.isInteger(normalizedLevelId) || normalizedLevelId <= 0) {
        showAlert('Invalid class id', 'error');
        return;
    }

    const level = allLevels.find(l => Number.parseInt(l.id, 10) === normalizedLevelId);
    if (!level) {
        showAlert('Class not found', 'error');
        return;
    }

    const currentIndex = allLevels.findIndex(l => Number.parseInt(l.id, 10) === normalizedLevelId);
    const fallbackLevel = allLevels[currentIndex + 1] || allLevels[currentIndex - 1] || null;

    const confirmed = confirm(`Delete ${level.level_name}? This will also remove linked sections, periods, and assignments.`);
    if (!confirmed) return;

    fetch(`/api/hierarchical-timetable/levels/${normalizedLevelId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const deletedTotal = data.cascade_deleted?.total || 0;
                const msg = deletedTotal > 0
                    ? `${data.message} (${deletedTotal} related record(s) removed)`
                    : (data.message || 'Class deleted successfully');

                currentLevelFilter = fallbackLevel ? Number.parseInt(fallbackLevel.id, 10) : null;
                showAlert(msg, 'success');
                loadAcademicLevels();
                loadAllSections();
                loadPeriods();
            } else {
                showAlert(data.error || 'Failed to delete class', 'error');
            }
        })
        .catch(err => showAlert('Error deleting class: ' + err.message, 'error'));
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

                // Refresh labels in periods table once sections are available
                renderPeriodsTable();
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
                    <button class="btn btn-sm text-primary hover-grow" onclick="editSection(${s.id})" title="Edit Section">
                        <i class="bi bi-pencil"></i>
                    </button>
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

    // Set modal to "Add" mode
    document.querySelector('#sectionModal .modal-title').textContent = 'Add New Section';
    document.querySelector('#sectionModal .btn-primary').textContent = 'Create Section';
    document.querySelector('#sectionModal .btn-primary').setAttribute('onclick', 'saveSection()');
    
    // Remove hidden ID field if it exists
    const hiddenId = document.getElementById('sectionEditId');
    if (hiddenId) hiddenId.remove();

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

function editSection(sectionId) {
    const section = allSections.find(s => s.id === sectionId);
    if (!section) {
        showAlert('Section not found', 'error');
        return;
    }

    // Populate form with section data
    document.getElementById('sectionLevelId').value = section.level_id;
    document.getElementById('sectionName').value = section.section_name;
    document.getElementById('sectionCapacity').value = section.capacity;

    // Add hidden input for section ID
    let hiddenId = document.getElementById('sectionEditId');
    if (!hiddenId) {
        hiddenId = document.createElement('input');
        hiddenId.type = 'hidden';
        hiddenId.id = 'sectionEditId';
        document.getElementById('sectionForm').appendChild(hiddenId);
    }
    hiddenId.value = sectionId;

    // Set modal to "Edit" mode
    document.querySelector('#sectionModal .modal-title').textContent = 'Edit Section';
    document.querySelector('#sectionModal .btn-primary').textContent = 'Update Section';
    document.querySelector('#sectionModal .btn-primary').setAttribute('onclick', 'updateSection()');

    // Show modal
    const modalEl = document.getElementById('sectionModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    modal.show();
}

function updateSection() {
    const sectionId = document.getElementById('sectionEditId').value;
    const sectionName = document.getElementById('sectionName').value;
    const capacity = document.getElementById('sectionCapacity').value;

    if (!sectionName) {
        showAlert('Please enter a section name', 'error');
        return;
    }

    fetch(`/api/hierarchical-timetable/sections/${sectionId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            section_name: sectionName,
            capacity: parseInt(capacity)
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Section updated successfully', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('sectionModal'));
                if (modal) modal.hide();
                loadAllSections();
            } else {
                showAlert(data.error || 'Failed to update section', 'error');
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

}

function onPeriodSectionChange() {
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
    const periodNumberInput = document.getElementById('periodNumber');
    if (!periodNumberInput) {
        return;
    }

    const levelId = document.getElementById('periodGrade').value;
    const sectionId = document.getElementById('periodSection').value;

    if (!levelId || !sectionId) {
        periodNumberInput.value = '';
        return;
    }

    fetch(`/api/timetable/next-period-number?level_id=${levelId}&section_id=${sectionId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                periodNumberInput.value = data.next_period_number;
            }
        });
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
    fetch(`/api/timetable/staff/list?school_id=${schoolId}`)
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
    const dayOfWeek = document.getElementById('daySelectAssign').value;
    const periodSelect = document.getElementById('periodSelectAssign');

    periodSelect.innerHTML = '<option value="">-- Loading... --</option>';

    if (!dayOfWeek || !levelId || !sectionId) {
        periodSelect.innerHTML = '<option value="">-- Choose Day, Grade, and Section --</option>';
        return;
    }

    // Fetch periods and current section allocations for the selected day.
    Promise.all([
        fetch(`/api/timetable/periods?school_id=${schoolId}&level_id=${levelId}&section_id=${sectionId}&day_of_week=${dayOfWeek}`).then(r => r.json()),
        fetch(`/api/hierarchical-timetable/section-schedule/${sectionId}`).then(r => r.json())
    ])
        .then(([periodData, sectionData]) => {
            if (!(periodData.success && periodData.periods)) {
                periodSelect.innerHTML = '<option value="">No periods defined for selected day</option>';
                return;
            }

            const periods = periodData.periods || [];
            if (!periods.length) {
                periodSelect.innerHTML = '<option value="">No periods defined for selected day</option>';
                return;
            }

            const dayInt = parseInt(dayOfWeek, 10);
            const sectionSchedule = sectionData.success && sectionData.data && Array.isArray(sectionData.data.schedule)
                ? sectionData.data.schedule
                : [];

            const allocatedPeriods = new Set(
                sectionSchedule
                    .filter(s => parseInt(s.day_of_week, 10) === dayInt)
                    .map(s => parseInt(s.period_number, 10))
            );

            periodSelect.innerHTML = '<option value="">-- Choose Period --</option>';
            periods.forEach(p => {
                const periodNumber = parseInt(p.period_number, 10);
                const isAllocated = allocatedPeriods.has(periodNumber);
                const label = `${p.period_name || `Period ${periodNumber}`} (${p.start_time}-${p.end_time})${isAllocated ? ' - Allocated' : ''}`;
                periodSelect.innerHTML += `<option value="${periodNumber}" data-id="${p.id}" ${isAllocated ? 'disabled' : ''}>${label}</option>`;
            });
        })
        .catch(err => {
            console.error('Error loading periods for assignment:', err);
            periodSelect.innerHTML = '<option value="">Error loading periods</option>';
        });
}

function onAssignDayChange() {
    // Re-evaluate available periods whenever day changes.
    onAssignSectionChange();
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

function downloadStaffPeriodTemplate() {
    window.location.href = '/api/hierarchical-timetable/staff-period/template';
}

function initStaffPeriodBulkUpload() {
    const form = document.getElementById('bulkUploadStaffPeriodForm');
    if (!form) return;

    form.addEventListener('submit', handleStaffPeriodBulkUpload);

    const modalEl = document.getElementById('bulkUploadStaffPeriodModal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', () => {
            const resultBox = document.getElementById('bulkStaffPeriodUploadResult');
            if (resultBox) {
                resultBox.className = 'd-none';
                resultBox.innerHTML = '';
            }
            form.reset();
        });
    }
}

function handleStaffPeriodBulkUpload(e) {
    e.preventDefault();

    const form = e.target;
    const fileInput = document.getElementById('bulkStaffPeriodFile');
    const submitBtn = document.getElementById('bulkStaffPeriodUploadSubmitBtn');
    const resultBox = document.getElementById('bulkStaffPeriodUploadResult');

    if (!fileInput || !fileInput.files || !fileInput.files.length) {
        showAlert('Please select an Excel/CSV file to upload.', 'error');
        return;
    }

    const formData = new FormData(form);

    const originalBtnHtml = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';

    resultBox.className = 'd-none';
    resultBox.innerHTML = '';

    fetch('/api/hierarchical-timetable/staff-period/bulk-upload', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                resultBox.className = 'alert alert-danger';
                resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${data.error || 'Bulk upload failed'}`;
                resultBox.classList.remove('d-none');
                return;
            }

            const createdCount = data.created_count || 0;
            const updatedCount = data.updated_count || 0;
            const totalRows = data.total_rows || 0;
            const skippedCount = data.skipped_count || 0;
            const errors = Array.isArray(data.errors) ? data.errors : [];

            let errorsHtml = '';
            if (errors.length) {
                const topErrors = errors.slice(0, 10).map(err => `<li>${err}</li>`).join('');
                const moreErrors = errors.length > 10 ? `<li>...and ${errors.length - 10} more error(s)</li>` : '';
                errorsHtml = `
                    <hr>
                    <div class="mb-1"><strong>Import issues:</strong></div>
                    <ul class="mb-0">${topErrors}${moreErrors}</ul>
                `;
            }

            resultBox.className = errors.length ? 'alert alert-warning' : 'alert alert-success';
            resultBox.innerHTML = `
                <div><strong>Bulk upload completed.</strong></div>
                <div>Created: ${createdCount} | Updated: ${updatedCount} | Skipped: ${skippedCount} | Total rows: ${totalRows}</div>
                ${errorsHtml}
            `;
            resultBox.classList.remove('d-none');

            if (createdCount > 0 || updatedCount > 0) {
                showAlert(`Bulk upload complete: ${createdCount} created, ${updatedCount} updated.`, 'success');
                const selectedStaffId = document.getElementById('staffSelectAssign')?.value;
                if (selectedStaffId) {
                    loadStaffCurrentAllocations(selectedStaffId);
                }
                loadStaffAssignmentsSummary();
            } else {
                showAlert('No allocations were imported. Check the file and try again.', 'error');
            }
        })
        .catch(err => {
            resultBox.className = 'alert alert-danger';
            resultBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Upload failed: ${err.message}`;
            resultBox.classList.remove('d-none');
            showAlert('Bulk upload failed. Please try again.', 'error');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
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
