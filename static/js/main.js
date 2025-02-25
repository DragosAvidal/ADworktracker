/**
 * Main JavaScript file for Employee Activity Tracker
 * Handles form interactions, report generation, and data export functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Initialize flatpickr date picker with Romanian locale and custom settings
     */
    flatpickr(".datepicker", {
        locale: "ro",
        dateFormat: "Y-m-d",
        defaultDate: "today",
        altInput: true,
        altFormat: "d F Y",
        theme: "material_blue",
        weekNumbers: true,
        animate: true,
        disableMobile: false
    });

    /**
     * Sets up the interaction between a select field and its corresponding "other" input field
     * @param {string} selectId - ID of the select element
     * @param {string} otherId - ID of the corresponding "other" input field
     */
    function setupOtherField(selectId, otherId) {
        const select = document.getElementById(selectId);
        const otherField = document.getElementById(otherId);
        
        if (select && otherField) {
            select.addEventListener('change', function() {
                otherField.classList.toggle('d-none', this.value !== 'other');
                if (this.value === 'other') {
                    otherField.required = true;
                    otherField.name = select.name;
                    select.name = select.name + '_original';
                } else {
                    otherField.required = false;
                    otherField.name = otherId;
                    select.name = select.name.replace('_original', '');
                }
            });
        }
    }

    setupOtherField('client', 'client_other');
    setupOtherField('project', 'project_other');
    setupOtherField('activity_type', 'activity_type_other');

    /**
     * Handle report form submissions and display results
     */
    const reportForms = document.querySelectorAll('.report-form');
    let currentReportType = '';
    let currentDate = '';
    reportForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            currentReportType = new FormData(this).get('report_type');
            currentDate = new FormData(this).get('date');
            try {
                const formData = new FormData(this);
                const response = await fetch(`/generate_report?${new URLSearchParams(formData)}`);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                let content = '';
                const reportType = formData.get('report_type');
                
                // Update export button texts based on report type
                const csvBtn = document.getElementById('exportCsvBtn');
                const excelBtn = document.getElementById('exportExcelBtn');
                if (reportType === 'monthly') {
                    csvBtn.textContent = 'Genereaza CSV lunar';
                    excelBtn.textContent = 'Genereaza Excel lunar';
                } else {
                    csvBtn.textContent = 'Export CSV sapt';
                    excelBtn.textContent = 'Export Excel sapt';
                }
                
                if (reportType === 'weekly' || reportType === 'monthly') {
                    content = `
                        <h4>Raport ${reportType === 'weekly' ? 'Săptămânal' : 'Lunar'}</h4>
                        <p>Perioada: ${data.start_date} - ${data.end_date}</p>
                        <p>Total ore: ${data.total_hours}</p>
                        
                        <h5 class="mt-4">Distribuție ore pe client:</h5>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Client</th>
                                        <th>Ore</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(data.hours_per_client)
                                        .map(([client, hours]) => 
                                            `<tr><td>${client}</td><td>${hours}</td></tr>`)
                                        .join('')}
                                </tbody>
                            </table>
                        </div>

                        <h5 class="mt-4">Distribuție ore pe proiect:</h5>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Proiect</th>
                                        <th>Ore</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(data.hours_per_project)
                                        .map(([project, hours]) => 
                                            `<tr><td>${project}</td><td>${hours}</td></tr>`)
                                        .join('')}
                                </tbody>
                            </table>
                        </div>

                        <h5 class="mt-4">Activități în perioada selectată:</h5>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Data</th>
                                        <th>Client</th>
                                        <th>Proiect</th>
                                        <th>Tip Activitate</th>
                                        <th>Ore</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.activities
                                        .map(activity => `
                                            <tr>
                                                <td>${activity.date}</td>
                                                <td>${activity.client}</td>
                                                <td>${activity.project}</td>
                                                <td>${activity.activity_type}</td>
                                                <td>${activity.hours}</td>
                                            </tr>`)
                                        .join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                }
                
                const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
                document.getElementById('reportContent').innerHTML = content;
                reportModal.show();
            } catch (error) {
                console.error('Error:', error);
                alert('A apărut o eroare la generarea raportului. Te rog încearcă din nou.');
            }
        });
    });

    const csvButton = document.getElementById('exportCsvBtn');
    const excelButton = document.getElementById('exportExcelBtn');

    function getExportUrl(format) {
        return `/export_report?report_type=${currentReportType}&date=${currentDate}&format=${format}`;
    }

    if (csvButton) {
        csvButton.addEventListener('click', function() {
            window.location.href = getExportUrl('csv');
        });
    }

    if (excelButton) {
        excelButton.addEventListener('click', function() {
            window.location.href = getExportUrl('excel');
        });
    }
});

/**
 * Generates and displays a client-based activity report
 * @param {Object} data - Report data from the server
 * @returns {void}
 */
function generateClientReport() {
    fetch('/generate_report?report_type=client')
        .then(response => response.json())
        .then(data => {
            // Afișare în modal
            let content = '<h4>Total Ore pe Client</h4><div class="table-responsive">';
            content += '<table class="table table-striped">';
            content += '<thead><tr><th>Client</th><th>Total Ore</th></tr></thead><tbody>';
            
            for (const [client, hours] of Object.entries(data.hours_per_client)) {
                content += `<tr><td>${client}</td><td>${hours}</td></tr>`;
            }
            
            content += '</tbody></table></div>';
            const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
            document.getElementById('reportContent').innerHTML = content;
            reportModal.show();

            // Afișare în secțiunea de rapoarte detaliate
            const detailsContent = JSON.stringify(data.hours_per_client, null, 2);
            document.querySelector('#clientReportDetails pre').textContent = detailsContent;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('A apărut o eroare la generarea raportului. Te rog încearcă din nou.');
        });
}

/**
 * Generates and displays a project-based activity report
 * @param {Object} data - Report data from the server
 * @returns {void}
 */
function generateProjectReport() {
    fetch('/generate_report?report_type=project')
        .then(response => response.json())
        .then(data => {
            // Afișare în modal
            let content = '<h4>Total Ore pe Proiect</h4><div class="table-responsive">';
            content += '<table class="table table-striped">';
            content += '<thead><tr><th>Proiect</th><th>Total Ore</th></tr></thead><tbody>';
            
            for (const [project, hours] of Object.entries(data.hours_per_project)) {
                content += `<tr><td>${project}</td><td>${hours}</td></tr>`;
            }
            
            content += '</tbody></table></div>';
            const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
            document.getElementById('reportContent').innerHTML = content;
            reportModal.show();

            // Afișare în secțiunea de rapoarte detaliate
            const detailsContent = JSON.stringify(data.hours_per_project, null, 2);
            document.querySelector('#projectReportDetails pre').textContent = detailsContent;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('A apărut o eroare la generarea raportului. Te rog încearcă din nou.');
        });
}

/**
 * Initiates the export of a report in the specified format
 * @param {string} reportType - Type of report to export ('client', 'project', 'weekly', 'monthly')
 * @param {string} format - Export format ('csv' or 'excel')
 * @returns {void}
 */
function exportReport(reportType, format) {
    let url = `/export_report?report_type=${reportType}&format=${format}`;
    
    // Adăugăm data pentru rapoartele săptămânale și lunare
    if (reportType === 'weekly' || reportType === 'monthly') {
        const dateInput = document.querySelector(`form input[name="date"][type="text"]`);
        if (dateInput && dateInput.value) {
            url += `&date=${dateInput.value}`;
        } else {
            alert('Vă rugăm selectați o dată pentru export.');
            return;
        }
    }
    
    // Descărcăm fișierul
    window.location.href = url;
}