(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var tbody_html = function(val, i){
        return `
            <td>${1}</td>
            <td>${1}</td>
            <td>${1}</td>
        `;
    }
    collection_check(tbody_html);
    $("[name*=q], #per_page").on("keyup paste change", function(){collection_check(tbody_html, 1, true);});
    var collection_manage = function(cmd, index){
        if (cmd == "edit") {
            //window.location = local_path + index + '/edit/';
        } else if (cmd == "delete") {
            
        }
    }
    $("#collection_modal_form").on("submit", function(e){
        e.preventDefault();
        var serializeform = $(this).serialize();
		var inputs = $(this).find("input, select, button, textarea");
		inputs.prop("disabled", true);
		$.ajax({
			type: "POST",
			url: $(this).attr("action"),
			data: serializeform,
			beforeSend: function(){},
			success: function(data){
				toastr.success(data["message"], {closeButton: true, progressBar: true,});
				inputs.prop("disabled", false);
				$(".modal").modal("hide");
				collection_check(tbody_html);
				//setTimeout(location.reload.bind(location), 2000);
			},
			error: function(jqXHR, textStatus, errorThrown){
				inputs.prop("disabled", false);
				toastr.error(JSON.parse(jqXHR.responseText)["message"], {closeButton: true, progressBar: true,});
			}
		});
    })
})(jQuery);