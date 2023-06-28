(function($){
    //var csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
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
})(jQuery);