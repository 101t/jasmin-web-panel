(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    $("li.nav-item.submit_logs-menu").addClass("active");
    
    var currentTaskId = null;
    var progressCheckInterval = null;
    
    // Function to get current filter values
    function getFilterValues() {
        return {
            search: $('#search').val(),
            status_filter: $('#status_filter').val(),
            date_column: $('#date_column').val(),
            date_from: $('#date_from').val(),
            date_to: $('#date_to').val()
        };
    }
    
    // Function to start export
    function startExport(format) {
        var filters = getFilterValues();
        
        // Show modal
        $('#exportProgressModal').modal('show');
        resetProgressModal();
        
        // Make AJAX request to start export
        $.ajax({
            url: export_url,
            type: 'POST',
            data: {
                format: format,
                search: filters.search,
                status_filter: filters.status_filter,
                date_column: filters.date_column,
                date_from: filters.date_from,
                date_to: filters.date_to,
                csrfmiddlewaretoken: csrfmiddlewaretoken
            },
            success: function(response) {
                if (response.status === 'started') {
                    currentTaskId = response.task_id;
                    updateProgressMessage(main_trans.export_started, 'primary');
                    startProgressCheck();
                } else {
                    updateProgressMessage(main_trans.export_error, 'danger');
                    stopProgressCheck();
                }
            },
            error: function() {
                updateProgressMessage(main_trans.export_error, 'danger');
                stopProgressCheck();
            }
        });
    }
    
    // Function to check progress
    function checkProgress() {
        if (!currentTaskId) return;
        
        var progressUrl = progress_url_template.replace('TASK_ID', currentTaskId);
        
        $.ajax({
            url: progressUrl,
            type: 'GET',
            success: function(data) {
                if (data.status === 'processing') {
                    updateProgressBar(data.progress || 0);
                    if (data.processed && data.total) {
                        $('#export-details').text(
                            main_trans.records_processed + ': ' + data.processed + ' / ' + data.total
                        );
                    }
                } else if (data.status === 'completed') {
                    updateProgressBar(100);
                    updateProgressMessage(main_trans.export_completed, 'success');
                    showDownloadButton();
                    stopProgressCheck();
                    if (data.total) {
                        $('#export-details').text(
                            main_trans.records_processed + ': ' + data.total
                        );
                    }
                } else if (data.status === 'failed') {
                    updateProgressMessage(main_trans.export_failed + ' ' + (data.error || ''), 'danger');
                    stopProgressCheck();
                } else if (data.status === 'not_found') {
                    updateProgressMessage(main_trans.export_error, 'warning');
                    stopProgressCheck();
                }
            },
            error: function() {
                updateProgressMessage(main_trans.export_error, 'danger');
                stopProgressCheck();
            }
        });
    }
    
    // Function to start progress checking
    function startProgressCheck() {
        if (progressCheckInterval) {
            clearInterval(progressCheckInterval);
        }
        progressCheckInterval = setInterval(checkProgress, 1000); // Check every second
    }
    
    // Function to stop progress checking
    function stopProgressCheck() {
        if (progressCheckInterval) {
            clearInterval(progressCheckInterval);
            progressCheckInterval = null;
        }
    }
    
    // Function to update progress bar
    function updateProgressBar(progress) {
        var $progressBar = $('#export-progress-bar');
        $progressBar.css('width', progress + '%');
        $progressBar.attr('aria-valuenow', progress);
        $progressBar.text(Math.round(progress) + '%');
    }
    
    // Function to update progress message
    function updateProgressMessage(message, type) {
        var iconClass = 'fas fa-spinner fa-spin';
        if (type === 'success') iconClass = 'fas fa-check-circle';
        else if (type === 'danger') iconClass = 'fas fa-times-circle';
        else if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';
        
        $('#export-status-message').html(
            '<i class="' + iconClass + ' fa-3x text-' + type + '"></i>' +
            '<p class="mt-3">' + message + '</p>'
        );
    }
    
    // Function to show download button
    function showDownloadButton() {
        $('#download-export-btn').show();
        $('#close-export-modal-btn').text('Close');
    }
    
    // Function to reset progress modal
    function resetProgressModal() {
        updateProgressBar(0);
        updateProgressMessage(main_trans.export_processing, 'primary');
        $('#download-export-btn').hide();
        $('#close-export-modal-btn').text('Close');
        $('#export-details').text('');
    }
    
    // Function to download file
    function downloadFile() {
        if (!currentTaskId) return;
        
        var downloadUrl = download_url_template.replace('TASK_ID', currentTaskId);
        window.location.href = downloadUrl;
        
        // Close modal after a short delay
        setTimeout(function() {
            $('#exportProgressModal').modal('hide');
        }, 1000);
    }
    
    // Event handlers
    $('#export-csv').on('click', function() {
        startExport('csv');
    });
    
    $('#export-xlsx').on('click', function() {
        startExport('xlsx');
    });
    
    $('#download-export-btn').on('click', function() {
        downloadFile();
    });
    
    // Clean up on modal close
    $('#exportProgressModal').on('hidden.bs.modal', function() {
        stopProgressCheck();
        currentTaskId = null;
    });
    
})(jQuery);