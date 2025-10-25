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
    const nodes = document.getElementById('nodes').value;
    const cpus = document.getElementById('cpus').value;
    const partition = document.getElementById('partition').value;

    if (!window.generatedConfigurations || window.generatedConfigurations.length === 0) {
        showStatus(statusDiv, 'Please generate parameter sweep first', 'error');
        statusDiv.style.display = 'block';
        return;
    }

    showStatus(statusDiv, `Submitting ${window.generatedConfigurations.length} jobs to cluster... This may take a few moments.`, 'info');
    statusDiv.style.display = 'block';

    try {
        const response = await fetch('/api/jobs/sweep/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                configurations: window.generatedConfigurations,
                nodes: parseInt(nodes),
                cpus_per_node: parseInt(cpus),
                partition: partition,
                xhpl_path: 'xhpl',  // Can be made configurable later
                time_limit: '01:00:00'  // Can be made configurable later
            })
        });

        const data = await response.json();

        if (response.ok) {
            let message = `✓ Sweep submitted successfully!\n`;
            message += `Sweep ID: ${data.sweep_id}\n`;
            message += `Sweep Name: ${data.sweep_name}\n`;
            message += `Jobs submitted: ${data.submitted_count}`;

            if (data.failed_count > 0) {
                message += `\nFailed: ${data.failed_count}`;
            }

            showStatus(statusDiv, message, 'success');

            // Show results section
            document.getElementById('results-section').style.display = 'block';

            // Display submitted jobs
            displaySubmittedJobs(data);

        } else {
            showStatus(statusDiv, `Error: ${data.detail || 'Sweep submission failed'}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Submission failed: ${error.message}`, 'error');
    }

    statusDiv.style.display = 'block';
}

// Display submitted jobs in results section
function displaySubmittedJobs(sweepData) {
    const resultsContent = document.getElementById('results-content');

    // Store current sweep ID for status monitoring
    window.currentSweepId = sweepData.sweep_id;

    let html = `
        <h3>Sweep Submitted: ${sweepData.sweep_name}</h3>
        <p><strong>Sweep ID:</strong> ${sweepData.sweep_id}</p>
        <p><strong>Jobs Submitted:</strong> ${sweepData.submitted_count}</p>
        ${sweepData.failed_count > 0 ? `<p class="error"><strong>Failed:</strong> ${sweepData.failed_count}</p>` : ''}
        <br>
        <button onclick="viewSweepStatus(${sweepData.sweep_id})" class="btn-secondary">View Job Status</button>
        <button onclick="startAutoRefresh(${sweepData.sweep_id})" class="btn-secondary">Auto-Refresh Status</button>
        <button onclick="stopAutoRefresh()" class="btn-secondary">Stop Refresh</button>
        <br><br>
        <h4>Submitted Jobs:</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Config #</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">SLURM Job ID</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">N</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">NB</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">P</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Q</th>
                </tr>
            </thead>
            <tbody>
    `;

    sweepData.submitted_jobs.forEach(job => {
        html += `
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.config_id}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.slurm_job_id}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.config.n}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.config.nb}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.config.p}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${job.config.q}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
        <div id="status-display" style="margin-top: 20px;"></div>
    `;

    resultsContent.innerHTML = html;
}

// View sweep status
async function viewSweepStatus(sweepId) {
    const statusDisplay = document.getElementById('status-display');

    statusDisplay.innerHTML = '<p>Loading job status...</p>';

    try {
        const response = await fetch(`/api/jobs/sweep/${sweepId}/status`);
        const data = await response.json();

        if (response.ok) {
            displaySweepStatus(data);
        } else {
            statusDisplay.innerHTML = `<p class="error">Error: ${data.detail || 'Failed to get status'}</p>`;
        }
    } catch (error) {
        statusDisplay.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }
}

// Display sweep status with job details
function displaySweepStatus(data) {
    const statusDisplay = document.getElementById('status-display');

    // Build status summary
    let html = `
        <h4>Job Status Summary</h4>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
            <p><strong>Last Updated:</strong> ${new Date().toLocaleString()}</p>
    `;

    // Display status counts
    if (data.status_counts) {
        html += '<p><strong>Status Breakdown:</strong></p><ul>';
        for (const [status, count] of Object.entries(data.status_counts)) {
            const color = getStatusColor(status);
            html += `<li><span style="color: ${color}; font-weight: bold;">${status}:</span> ${count}</li>`;
        }
        html += '</ul>';
    }

    html += '</div>';

    // Job details table
    html += `
        <h4>Job Details</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 6px; border: 1px solid #ddd;">Job ID</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Status</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">N</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">NB</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">P×Q</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Time</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.jobs.forEach(job => {
        const status = job.current_status || job.status;
        const color = getStatusColor(status);
        const timeInfo = job.time_used || job.time_left || '-';

        html += `
            <tr>
                <td style="padding: 6px; border: 1px solid #ddd;">${job.slurm_job_id}</td>
                <td style="padding: 6px; border: 1px solid #ddd; color: ${color}; font-weight: bold;">${status}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">${job.n}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">${job.nb}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">${job.p}×${job.q}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">${timeInfo}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    statusDisplay.innerHTML = html;
}

// Get color for job status
function getStatusColor(status) {
    const statusColors = {
        'PENDING': '#FFA500',
        'RUNNING': '#0066CC',
        'COMPLETED': '#28A745',
        'FAILED': '#DC3545',
        'CANCELLED': '#6C757D',
        'TIMEOUT': '#DC3545',
        'NOT_FOUND': '#6C757D',
        'SUBMITTED': '#17A2B8'
    };
    return statusColors[status] || '#333';
}

// Auto-refresh functionality
let autoRefreshInterval = null;

function startAutoRefresh(sweepId) {
    // Stop any existing refresh
    stopAutoRefresh();

    // Initial update
    viewSweepStatus(sweepId);

    // Set up interval (refresh every 10 seconds)
    autoRefreshInterval = setInterval(() => {
        viewSweepStatus(sweepId);
    }, 10000);

    console.log('Auto-refresh started for sweep', sweepId);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}
