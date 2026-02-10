// Test Department Shift Mappings Display
// This script will simulate multiple department mappings to test the 3-card layout

console.log('🧪 Testing Department Shift Mappings Layout');

// Mock data with more than 3 mappings
const testMappings = [
    { department: 'Human Resources', default_shift_type: 'general', created_at: '2024-01-15', updated_at: '2024-01-15' },
    { department: 'Information Technology', default_shift_type: 'morning', created_at: '2024-01-16', updated_at: '2024-01-16' },
    { department: 'Finance', default_shift_type: 'general', created_at: '2024-01-17', updated_at: '2024-01-17' },
    { department: 'Marketing', default_shift_type: 'evening', created_at: '2024-01-18', updated_at: '2024-01-18' },
    { department: 'Operations', default_shift_type: 'night', created_at: '2024-01-19', updated_at: '2024-01-19' },
    { department: 'Sales', default_shift_type: 'general', created_at: '2024-01-20', updated_at: '2024-01-20' },
    { department: 'Customer Service', default_shift_type: 'morning', created_at: '2024-01-21', updated_at: '2024-01-21' },
    { department: 'Research & Development', default_shift_type: 'general', created_at: '2024-01-22', updated_at: '2024-01-22' }
];

// Function to test the layout
function testDepartmentShiftLayout() {
    console.log(`📊 Testing with ${testMappings.length} department mappings`);
    
    // Check if the function exists
    if (typeof renderDepartmentShiftMappings === 'function') {
        renderDepartmentShiftMappings(testMappings);
        console.log('✅ Layout test completed');
        
        // Count the rendered cards
        const renderedCards = document.querySelectorAll('#departmentShiftMappings .dept-shift-card');
        console.log(`📋 Cards rendered: ${renderedCards.length}`);
        
        // Check the grid layout
        const columns = document.querySelectorAll('#departmentShiftMappings .col-xl-4');
        console.log(`🔳 Column elements: ${columns.length}`);
        
        if (renderedCards.length === testMappings.length) {
            console.log('✅ All mappings displayed correctly');
        } else {
            console.log('❌ Some mappings are missing');
        }
        
        // Check responsive classes
        columns.forEach((col, index) => {
            const classes = col.className;
            if (classes.includes('col-xl-4') && classes.includes('col-lg-4') && classes.includes('col-md-6')) {
                console.log(`✅ Card ${index + 1}: Correct responsive classes`);
            } else {
                console.log(`❌ Card ${index + 1}: Missing responsive classes`);
            }
        });
        
    } else {
        console.log('❌ renderDepartmentShiftMappings function not found');
    }
}

// Run the test when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testDepartmentShiftLayout);
} else {
    testDepartmentShiftLayout();
}

console.log('🎯 Test script loaded. Run testDepartmentShiftLayout() to test the layout.');
