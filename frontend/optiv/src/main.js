document.getElementById('analyzeButton').addEventListener('click', () => {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const resultsArea = document.getElementById('resultsArea');
    const findingsDiv = document.getElementById('findings');
    const spinner = document.getElementById('spinner');

    if (!file) {
        alert("Please select a file first!");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // Show the results area and the spinner by removing the 'hidden' class
    resultsArea.classList.remove('hidden');
    spinner.classList.remove('hidden');
    findingsDiv.innerHTML = '';

    fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        spinner.classList.add('hidden'); // Hide spinner by adding the 'hidden' class back
        
        if (data.error) {
            findingsDiv.innerHTML = `<p class="text-red-600">Error: ${data.error}</p>`;
        } else {
            let findingsHTML = '<ul class="space-y-2">';
            data.key_findings.forEach(finding => {
                findingsHTML += `<li class="bg-blue-50 p-3 rounded-md">${finding}</li>`;
            });
            findingsHTML += '</ul>';
            findingsDiv.innerHTML = findingsHTML;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        spinner.classList.add('hidden');
        findingsDiv.innerHTML = `<p class="text-red-600">An error occurred. Make sure the backend server is running.</p>`;
    });
});