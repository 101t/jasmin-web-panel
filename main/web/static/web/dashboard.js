(function($){
    //var csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    
    // Gateway state check
    var gw_state = function() {
		$.ajax({
			type: "GET",
			url: window.location.pathname + 'manage/',
			data: {s: 'gw_state'},
			beforeSend: function(){},
			success: function(data){
			    if (data.status) {
			        toastr.success(data["message"], {closeButton: true, progressBar: true,});
			    } else {
			        toastr.warning(data["message"], {closeButton: true, progressBar: true,});
			    }
                $("#binding_status").removeClass("bg-secondary").addClass(data.status? 'bg-success' : 'bg-warning');
                $("#binding_status_text").text(data.message);
			},
			error: function(jqXHR, textStatus, errorThrown){
				toastr.error(JSON.parse(jqXHR.responseText)["message"], {closeButton: true, progressBar: true,});
			}
		});
    }
    gw_state();
    
    // Chart.js Configuration
    var timelineChart = null;
    var donutChart = null;
    var currentGrouping = 'daily';
    
    // Initialize Timeline Chart
    function initTimelineChart(labels, successData, failedData) {
        var ctx = document.getElementById('timelineChart');
        if (!ctx) return;
        
        // Destroy existing chart if exists
        if (timelineChart) {
            timelineChart.destroy();
        }
        
        timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Success',
                        data: successData,
                        borderColor: 'rgb(28, 200, 138)',
                        backgroundColor: 'rgba(28, 200, 138, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: 'Failed',
                        data: failedData,
                        borderColor: 'rgb(231, 74, 59)',
                        backgroundColor: 'rgba(231, 74, 59, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // Initialize Donut Chart
    function initDonutChart(successCount, failedCount, unknownCount) {
        var ctx = document.getElementById('donutChart');
        if (!ctx) return;
        
        // Destroy existing chart if exists
        if (donutChart) {
            donutChart.destroy();
        }
        
        donutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Success', 'Failed', 'Unknown'],
                datasets: [{
                    data: [successCount, failedCount, unknownCount],
                    backgroundColor: [
                        'rgb(28, 200, 138)',
                        'rgb(231, 74, 59)',
                        'rgb(133, 135, 150)'
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                var label = context.label || '';
                                var value = context.parsed || 0;
                                var total = context.dataset.data.reduce((a, b) => a + b, 0);
                                var percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return label + ': ' + value.toLocaleString() + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Load timeline data based on grouping
    function loadTimelineData(grouping) {
        $.ajax({
            type: "GET",
            url: window.location.pathname + 'manage/',
            data: {
                s: 'submit_log_timeline',
                grouping: grouping
            },
            beforeSend: function() {
                // Show loading state
                $('.grouping-buttons button').prop('disabled', true);
            },
            success: function(data) {
                if (data.status === 'success') {
                    initTimelineChart(data.labels, data.success, data.failed);
                    currentGrouping = grouping;
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Failed to load timeline data:', errorThrown);
            },
            complete: function() {
                $('.grouping-buttons button').prop('disabled', false);
            }
        });
    }
    
    // Initialize charts with data from Django
    if (typeof chartData !== 'undefined') {
        // Initialize timeline chart with initial data
        initTimelineChart(
            chartData.timeline.labels,
            chartData.timeline.success,
            chartData.timeline.failed
        );
        
        // Initialize donut chart
        initDonutChart(
            chartData.donut.success,
            chartData.donut.failed,
            chartData.donut.unknown
        );
    }
    
    // Grouping button click handlers
    $('.grouping-buttons button').on('click', function() {
        var grouping = $(this).data('grouping');
        
        // Update button states
        $('.grouping-buttons button').removeClass('active');
        $(this).addClass('active');
        
        // Load new data
        loadTimelineData(grouping);
    });
    
})(jQuery);