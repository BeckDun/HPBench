// HPL-Sweep Frontend Application

// Check API health on load
window.onload = async function() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.error('Failed to connect to API:', error);
    }
};

// Connect to SSH
async function connectSSH() {
    const hostname = document.getElementById('hostname').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const statusDiv = document.getElementById('ssh-status');

    if (!hostname || !username || !password) {
        showStatus(statusDiv, 'Please fill in all fields', 'error');
        return;
    }

    showStatus(statusDiv, 'Connecting...', 'info');

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ hostname, username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, 'Connected successfully!', 'success');
            document.getElementById('job-section').style.display = 'block';

            // Load available partitions
            await loadPartitions();
        } else {
            showStatus(statusDiv, `Error: ${data.detail || 'Connection failed'}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Connection failed: ${error.message}`, 'error');
    }
}

// Load available partitions from cluster
async function loadPartitions() {
    const partitionSelect = document.getElementById('partition');

    try {
        const response = await fetch('/api/cluster/partitions');
        const data = await response.json();

        if (response.ok) {
            // Clear existing options
            partitionSelect.innerHTML = '';

            // Add partitions to dropdown
            if (data.partitions && data.partitions.length > 0) {
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select a partition...';
                partitionSelect.appendChild(defaultOption);

                // Add partition options
                data.partitions.forEach(partition => {
                    const option = document.createElement('option');
                    option.value = partition;
                    option.textContent = partition;
                    partitionSelect.appendChild(option);
                });

                console.log(`Loaded ${data.partitions.length} partitions:`, data.partitions);
            } else {
                partitionSelect.innerHTML = '<option value="">No partitions found</option>';
            }
        } else {
            console.error('Failed to load partitions:', data.detail);
            partitionSelect.innerHTML = '<option value="">Failed to load partitions</option>';
        }
    } catch (error) {
        console.error('Error loading partitions:', error);
        partitionSelect.innerHTML = '<option value="">Error loading partitions</option>';
    }
}

// Test SLURM configuration
async function testSlurmConfig() {
    const nodes = document.getElementById('nodes').value;
    const cpus = document.getElementById('cpus').value;
    const partition = document.getElementById('partition').value;
    const testStatusDiv = document.getElementById('test-status');
    const testOutputDiv = document.getElementById('test-output');

    // Validate inputs
    if (!partition) {
        showStatus(testStatusDiv, 'Please select a partition', 'error');
        testStatusDiv.style.display = 'block';
        testOutputDiv.style.display = 'none';
        return;
    }

    if (!nodes || nodes < 1) {
        showStatus(testStatusDiv, 'Please specify at least 1 node', 'error');
        testStatusDiv.style.display = 'block';
        testOutputDiv.style.display = 'none';
        return;
    }

    if (!cpus || cpus < 1) {
        showStatus(testStatusDiv, 'Please specify at least 1 CPU per node', 'error');
        testStatusDiv.style.display = 'block';
        testOutputDiv.style.display = 'none';
        return;
    }

    // Show status message
    showStatus(testStatusDiv, 'Submitting test job... This may take up to 60 seconds.', 'info');
    testStatusDiv.style.display = 'block';
    testOutputDiv.style.display = 'none';

    try {
        const response = await fetch('/api/jobs/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nodes: parseInt(nodes),
                cpus_per_node: parseInt(cpus),
                partition: partition
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Test completed successfully
            if (data.test_passed) {
                showStatus(testStatusDiv, `✓ Test PASSED! Job ID: ${data.job_id}`, 'success');

                // Show HPL parameters section after successful test
                document.getElementById('hpl-params-section').style.display = 'block';
            } else {
                showStatus(testStatusDiv, `✗ Test FAILED! Job ID: ${data.job_id}`, 'error');
            }

            // Display output
            testOutputDiv.innerHTML = `
                <h4>Test Job Output:</h4>
                <div><strong>Job ID:</strong> ${data.job_id}</div>
                <div><strong>Job State:</strong> ${data.job_state}</div>
                <div><strong>Configuration:</strong> ${data.nodes} node(s), ${data.cpus_per_node} CPU(s) per node, Partition: ${data.partition}</div>
                <div><strong>Result:</strong> ${data.test_passed ? '✓ PASSED' : '✗ FAILED'}</div>
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #dee2e6;">
                <div><strong>Output:</strong></div>
                <pre style="margin: 5px 0;">${data.output}</pre>
            `;
            testOutputDiv.style.display = 'block';

        } else {
            showStatus(testStatusDiv, `Error: ${data.detail || 'Test job failed'}`, 'error');
            testOutputDiv.style.display = 'none';
        }
    } catch (error) {
        showStatus(testStatusDiv, `Test failed: ${error.message}`, 'error');
        testOutputDiv.style.display = 'none';
    }

    testStatusDiv.style.display = 'block';
}

// Submit job
async function submitJob() {
    const nodes = document.getElementById('nodes').value;
    const cpus = document.getElementById('cpus').value;
    const partition = document.getElementById('partition').value;
    const statusDiv = document.getElementById('job-status');

    if (!partition) {
        showStatus(statusDiv, 'Please specify a partition', 'error');
        return;
    }

    showStatus(statusDiv, 'Submitting job...', 'info');

    try {
        const response = await fetch('/api/jobs/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nodes, cpus, partition })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, `Job submitted successfully! Job ID: ${data.job_id}`, 'success');
            document.getElementById('results-section').style.display = 'block';
        } else {
            showStatus(statusDiv, `Error: ${data.detail || 'Job submission failed'}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Job submission failed: ${error.message}`, 'error');
    }
}

// Helper function to show status messages
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
}

// Load recommended P x Q values
async function loadRecommendedPQ() {
    const nodes = document.getElementById('nodes').value;
    const cpus = document.getElementById('cpus').value;
    const pqRecommendations = document.getElementById('pq-recommendations');

    const totalProcesses = parseInt(nodes) * parseInt(cpus);

    try {
        const response = await fetch(`/api/jobs/parameters/recommended-pq/${totalProcesses}`);
        const data = await response.json();

        if (response.ok) {
            let html = `<strong>Recommended P x Q for ${totalProcesses} processes:</strong><br>`;
            html += `<small>${data.description}</small><br><br>`;

            data.pq_pairs.forEach(pair => {
                html += `<div class="pq-option" onclick="selectPQ(${pair[0]}, ${pair[1]})">`;
                html += `P=${pair[0]}, Q=${pair[1]}`;
                html += `</div>`;
            });

            pqRecommendations.innerHTML = html;
            pqRecommendations.style.display = 'block';
        }
    } catch (error) {
        console.error('Failed to load P x Q recommendations:', error);
    }
}

// Select P and Q values
function selectPQ(p, q) {
    document.getElementById('p-values').value = p;
    document.getElementById('q-values').value = q;
    alert(`Selected P=${p}, Q=${q}`);
}

// Generate parameter sweep preview
async function generateParameterSweep() {
    const statusDiv = document.getElementById('param-status');
    const summaryDiv = document.getElementById('param-summary');
    const summaryContent = document.getElementById('param-summary-content');

    // Get parameter values
    const nStart = parseInt(document.getElementById('n-start').value);
    const nEnd = parseInt(document.getElementById('n-end').value);
    const nStep = parseInt(document.getElementById('n-step').value);

    // Get selected NB values
    const nbSelect = document.getElementById('nb-values');
    const nbValues = Array.from(nbSelect.selectedOptions).map(opt => parseInt(opt.value));

    // Get P and Q values
    const pValues = document.getElementById('p-values').value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
    const qValues = document.getElementById('q-values').value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));

    // Validation
    if (nbValues.length === 0) {
        showStatus(statusDiv, 'Please select at least one NB value', 'error');
        statusDiv.style.display = 'block';
        return;
    }

    if (pValues.length === 0 || qValues.length === 0) {
        showStatus(statusDiv, 'Please specify P and Q values', 'error');
        statusDiv.style.display = 'block';
        return;
    }

    showStatus(statusDiv, 'Generating parameter sweep...', 'info');
    statusDiv.style.display = 'block';

    try {
        const response = await fetch('/api/jobs/parameters/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                parameter_range: {
                    n_start: nStart,
                    n_end: nEnd,
                    n_step: nStep,
                    nb_values: nbValues,
                    p_values: pValues,
                    q_values: qValues
                },
                max_combinations: 100
            })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, `✓ Generated ${data.total_configurations} configurations`, 'success');

            // Show summary
            summaryContent.innerHTML = `
                <strong>Total Configurations:</strong> ${data.total_configurations}<br>
                <strong>N Range:</strong> ${nStart} to ${nEnd} (step ${nStep})<br>
                <strong>NB Values:</strong> ${nbValues.join(', ')}<br>
                <strong>P Values:</strong> ${pValues.join(', ')}<br>
                <strong>Q Values:</strong> ${qValues.join(', ')}<br>
                <br>
                <small>Click "Submit Parameter Sweep" to run these configurations on the cluster.</small>
            `;
            summaryDiv.style.display = 'block';

            // Store configurations for submission
            window.generatedConfigurations = data.configurations;

        } else {
            showStatus(statusDiv, `Error: ${data.detail || 'Failed to generate parameters'}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }

    statusDiv.style.display = 'block';
}

// Submit parameter sweep
async function submitParameterSweep() {
    const statusDiv = document.getElementById('param-status');

    if (!window.generatedConfigurations || window.generatedConfigurations.length === 0) {
        showStatus(statusDiv, 'Please generate parameter sweep first', 'error');
        statusDiv.style.display = 'block';
        return;
    }

    showStatus(statusDiv, `Submitting ${window.generatedConfigurations.length} configurations...`, 'info');
    statusDiv.style.display = 'block';

    // TODO: Implement actual job submission in next step
    setTimeout(() => {
        showStatus(statusDiv, 'Parameter sweep submission will be implemented in the next step!', 'info');
        document.getElementById('results-section').style.display = 'block';
    }, 1000);
}
