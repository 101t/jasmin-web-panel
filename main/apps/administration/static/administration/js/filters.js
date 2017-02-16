$(function(){
	window.Filters_Dict = {};
	window.htmlEscape = function(str) {
	    return str
	        .replace(/&/g, '&amp;')
	        .replace(/"/g, '&quot;')
	        .replace(/'/g, '&#39;')
	        .replace(/</g, '&lt;')
	        .replace(/>/g, '&gt;');
	}
	window.filters_view_list = function(){
		var urlto = $("input[name=urlto]").val();
		$.ajax({
			type: "POST",
			url: urlto,
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				console.log(JSON.stringify(data));
				var filters = data["filters"];
				var output = "";
				var counter = 1;
				$.each(filters, function(i, v){
					output += "<tr>";
					output += "<td>" + counter + "</td>";
					output += "<td>" + v["fid"] + "</td>";
					output += "<td>" + v["type"] + "</td>";
					output += "<td>" + v["routes"] + "</td>";
					output += "<td>" + htmlEscape(v["description"]) + "</td>";
					output += '<td class="text-center" style="padding-top:4px;padding-bottom:4px;">'+
					'<div class="btn-group btn-group-xs">'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return filters_view_manage(\'delete\', \'' + counter + '\');"><i class="fa fa-trash"></i></a>'+
					'</div>'+
					'</td>';
					output += "</tr>";
					Filters_Dict[counter] = v;
					counter += 1;
				});
				$("#table_result").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	filters_view_list();
	window.filters_view_manage = function(act, counter){
		if(act === "delete"){
			var data = Filters_Dict[counter];
			var result = confirm("Do you want to delete?");
			if (result) {
				var urlto = $("input[name=urlto]").val();
			    $.ajax({
					type: "POST",
					url: urlto,
					data: {s:"delete", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, fid: data.fid},
					cache: false,
					dataType: "json",
					success: function(data){
						filters_view_list();
					},
					error: function(jqXHR, textStatus, errorThrown){
		                //alert(errorThrown);
		            }
				});
			}
		}
	}
	$("#add_filters_form").submit(function(event){
		event.preventDefault();
		var serializedform = $(this).serialize();
		var $inputs = $(this).find("input, select, button, textarea");
		$inputs.prop("disabled", true);
		$.ajax({
			type: "POST",
			url: $(this).attr("action"),
			data: serializedform,
			cache: false,
			beforeSend: function(){},
			success: function(data){
				$inputs.prop("disabled", false);
				filters_view_list();
				$("#add_filters_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
                location.reload();
            }
		});
	});
});