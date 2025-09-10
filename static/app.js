/**
 * JavaScript for Python AI Tutor Web Application
 * Handles code execution, progress tracking, and UI interactions
 */

// Global variables
let isExecuting = false;

/**
 * Execute Python code and display output in result div
 */
function runCode(code, outputElementId = 'code-output') {
    if (isExecuting) {
        return;
    }
    
    if (!code || !code.trim()) {
        showNotification('Please enter some code to run!', 'warning');
        return;
    }
    
    isExecuting = true;
    updateExecutionStatus('running', 'Running code...');
    
    // Show loading state
    const runButton = document.getElementById('run-button');
    if (runButton) {
        runButton.classList.add('is-loading');
        runButton.disabled = true;
    }
    
    // Make API request
    fetch('/api/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code })
    })
    .then(response => response.json())
    .then(data => {
        displayCodeOutput(data, outputElementId);
        updateExecutionStatus(data.success ? 'success' : 'error', 
                            data.success ? 'Code executed successfully' : 'Execution failed',
                            data.execution_time);
    })
    .catch(error => {
        console.error('Error executing code:', error);
        displayCodeOutput({
            success: false,
            stderr: `Network error: ${error.message}`,
            stdout: ''
        }, outputElementId);
        updateExecutionStatus('error', 'Network error occurred');
    })
    .finally(() => {
        isExecuting = false;
        if (runButton) {
            runButton.classList.remove('is-loading');
            runButton.disabled = false;
        }
    });
}

/**
 * Display code execution output in the UI
 */
function displayCodeOutput(result, outputElementId) {
    const outputDiv = document.getElementById(outputElementId);
    const outputContent = document.getElementById('output-content');
    
    if (!outputDiv || !outputContent) {
        console.error('Output elements not found');
        return;
    }
    
    let outputText = '';
    let outputClass = 'has-text-light';
    
    if (result.success) {
        if (result.stdout && result.stdout.trim()) {
            outputText = result.stdout;
            outputClass = 'has-text-success';
        } else {
            outputText = '(No output)';
            outputClass = 'has-text-grey-light';
        }
    } else {
        outputText = result.stderr || result.error || 'Unknown error occurred';
        outputClass = 'has-text-danger';
    }
    
    outputContent.textContent = outputText;
    outputContent.className = outputClass;
    outputDiv.style.display = 'block';
}

/**
 * Update execution status display
 */
function updateExecutionStatus(status, message, executionTime = null) {
    const statusDiv = document.getElementById('execution-status');
    const statusText = document.getElementById('status-text');
    const timeSpan = document.getElementById('execution-time');
    
    if (!statusDiv || !statusText) return;
    
    // Update status message
    statusText.textContent = message;
    
    // Update execution time
    if (timeSpan && executionTime !== null) {
        timeSpan.textContent = `${(executionTime * 1000).toFixed(0)}ms`;
        timeSpan.style.display = 'inline';
    } else if (timeSpan) {
        timeSpan.style.display = 'none';
    }
    
    // Update notification style
    const notification = statusDiv.querySelector('.notification');
    if (notification) {
        notification.className = 'notification ' + getStatusClass(status);
    }
    
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages
    if (status === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

/**
 * Get CSS class for execution status
 */
function getStatusClass(status) {
    switch (status) {
        case 'success': return 'is-success is-light';
        case 'error': return 'is-danger is-light';
        case 'running': return 'is-info is-light';
        default: return 'is-light';
    }
}

/**
 * Save progress to backend
 */
function updateProgress(topicId, level, score = 1.0, timeSpent = 0) {
    fetch('/update_progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic_id: topicId,
            level: level,
            score: score,
            time_spent: timeSpent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Progress saved successfully');
            
            // Show celebration message for streak milestones
            if (data.celebration) {
                showNotification(data.celebration, 'success', 8000);
            }
        } else {
            console.error('Failed to save progress:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving progress:', error);
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification is-${type}`;
    notification.innerHTML = `
        <button class="delete" onclick="this.parentElement.remove()"></button>
        ${message}
    `;
    
    // Add to page
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
}

/**
 * Progressive hint disclosure for challenges
 */
function showHint(hintNumber, totalHints) {
    const hintElement = document.getElementById(`hint-${hintNumber}`);
    if (hintElement) {
        hintElement.style.display = 'block';
        
        // Update hint button
        const hintButton = document.getElementById(`hint-button-${hintNumber}`);
        if (hintButton) {
            hintButton.textContent = `Hide Hint ${hintNumber}`;
            hintButton.onclick = () => hideHint(hintNumber, totalHints);
        }
        
        // Show next hint button if available
        if (hintNumber < totalHints) {
            const nextHintButton = document.getElementById(`hint-button-${hintNumber + 1}`);
            if (nextHintButton) {
                nextHintButton.style.display = 'inline-block';
            }
        }
    }
}

/**
 * Hide hint
 */
function hideHint(hintNumber, totalHints) {
    const hintElement = document.getElementById(`hint-${hintNumber}`);
    if (hintElement) {
        hintElement.style.display = 'none';
        
        // Update hint button
        const hintButton = document.getElementById(`hint-button-${hintNumber}`);
        if (hintButton) {
            hintButton.textContent = `Show Hint ${hintNumber}`;
            hintButton.onclick = () => showHint(hintNumber, totalHints);
        }
    }
}

/**
 * Auto-save progress periodically
 */
function startAutoSave(topicId, level) {
    const startTime = Date.now();
    
    setInterval(() => {
        const timeSpent = Math.floor((Date.now() - startTime) / 1000);
        updateProgress(topicId, level, 1.0, timeSpent);
    }, 30000); // Save every 30 seconds
}

/**
 * Load topic content dynamically (for future AJAX loading)
 */
function loadTopicContent(topicId, level = 0) {
    return fetch(`/api/topics/${topicId}`)
        .then(response => response.json())
        .then(data => {
            if (data.topic) {
                return data.topic;
            } else {
                throw new Error(data.error || 'Failed to load topic');
            }
        });
}

/**
 * Copy code to clipboard
 */
function copyCode(codeElement) {
    const code = codeElement.textContent;
    navigator.clipboard.writeText(code).then(() => {
        showNotification('Code copied to clipboard!', 'success', 2000);
    }).catch(err => {
        console.error('Failed to copy code: ', err);
        showNotification('Failed to copy code', 'danger', 3000);
    });
}

/**
 * Format code in textarea (basic indentation)
 */
function formatCode(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    
    const code = textarea.value;
    const lines = code.split('\n');
    let indentLevel = 0;
    const formattedLines = [];
    
    for (let line of lines) {
        const trimmed = line.trim();
        
        // Decrease indent for certain keywords
        if (trimmed.startsWith(('else:', 'elif ', 'except:', 'finally:'))) {
            indentLevel = Math.max(0, indentLevel - 1);
        }
        
        // Add current line with proper indentation
        if (trimmed) {
            formattedLines.push('    '.repeat(indentLevel) + trimmed);
        } else {
            formattedLines.push('');
        }
        
        // Increase indent after certain keywords
        if (trimmed.endsWith(':')) {
            indentLevel++;
        }
    }
    
    textarea.value = formattedLines.join('\n');
    showNotification('Code formatted!', 'info', 2000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Python AI Tutor - Web Application loaded');
    
    // Add keyboard shortcuts globally
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / for help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
    });
    
    // Initialize syntax highlighting if Prism is available
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
});

/**
 * Show keyboard shortcuts help
 */
function showKeyboardShortcuts() {
    const shortcuts = `
Keyboard Shortcuts:
• Ctrl/Cmd + Enter: Run code
• Ctrl/Cmd + /: Show this help
• Tab: Indent code (in text areas)
• Shift + Tab: Unindent code
    `;
    alert(shortcuts);
}