document.getElementById('eligibilityForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission

    const patientId = document.getElementById('patientId').value.trim();
    const outputSection = document.getElementById('outputSection');
    outputSection.innerHTML = ''; // Clear previous content

    if (patientId) {
        // Make a request to fetch the reports for the given Patient ID
        fetch(`/fetch_patient_reports?patientID=${patientId}`)
        .then(response => response.json())
        .then(data => {
            // Check if there's an error
            if (data.error) {
                outputSection.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }

            // Iterate over each report and create boxes dynamically
            data.forEach((record, index) => {
                const reportBox = document.createElement('div');
                reportBox.className = 'result-box p-3 mb-3 border rounded';
                reportBox.innerHTML = `<h5>Record ${index + 1}</h5><pre>${record.GeneratedReport}</pre>`;
                outputSection.appendChild(reportBox);
            });
        })
        .catch(error => {
            console.error('Error fetching reports:', error);
            outputSection.innerHTML = `<div class="alert alert-danger">Error fetching reports</div>`;
        });
    }
});
