$(function() {
	window.MTRouter_Dict = {};
	window.SMPPCCM_Dict = {};
	window.load_smppconnectors_in_select = function(){
		var urltosmppccm = $("input[name=urltosmppccm]").val();
		$.ajax({
			url: urltosmppccm,
			type: "POST",
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var smppccm = data["connectors"];
				var output = "";
				var counter = 1;
				$.each(smppccm, function(i, v){
					output += "<option>" + v.cid + "</option>";
					SMPPCCM_Dict[counter] = v;
					counter += 1;
				});
				$("#smppconnectors_select").html(output);
				$('.selectpicker').selectpicker('refresh');
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	load_smppconnectors_in_select();
	window.HTTPCCM_Dict = {};
	window.load_httpconnectors_in_select = function(){
		var urltohttpccm = $("input[name=urltohttpccm]").val();
		$.ajax({
			url: urltohttpccm,
			type: "POST",
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var httpccm = data["connectors"];
				var output = "";
				var counter = 1;
				$.each(httpccm, function(i, v){
					output += "<option>" + v.cid + "</option>";
					HTTPCCM_Dict[counter] = v;
					counter += 1;
				});
				$("#httpconnectors_select").html(output);
				$('.selectpicker').selectpicker('refresh');
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	load_httpconnectors_in_select();
	window.Filters_Dict = {};
	window.load_filters_in_select = function(){
		var urltofilters = $("input[name=urltofilters]").val();
		$.ajax({
			url: urltofilters,
			type: "POST",
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var filters = data["filters"];
				var output = "";
				var counter = 1;
				$.each(filters, function(i, v){
					output += "<option>" + v.fid + "</option>";
					Filters_Dict[counter] = v;
					counter += 1;
				});
				$("#filters_select").html(output);
				$('.selectpicker').selectpicker('refresh');
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	load_filters_in_select();
	window.htmlEscape = function(str) {
		return str
	        .replace(/&/g, '&amp;')
	        .replace(/"/g, '&quot;')
	        .replace(/'/g, '&#39;')
	        .replace(/</g, '&lt;')
	        .replace(/>/g, '&gt;');
	}
	window.mtrouter_view_list = function(){
		var urlto = $("input[name=urlto]").val();
		$.ajax({
			type: "POST",
			url: urlto,
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				//console.log(JSON.stringify(data));
				var mtrouter = data["mtrouters"];
				var output = "";
				var counter = 1;
				$.each(mtrouter, function(i, v){
					output += "<tr>";
					output += "<td>" + counter + "</td>";
					output += "<td>" + v["order"] + "</td>";
					output += "<td>" + v["type"] + "</td>";
					output += "<td>" + v["rate"] + "</td>";
					output += "<td>" + JSON.stringify(v["connectors"]) + "</td>";
					output += "<td>" + htmlEscape(JSON.stringify(v["filters"])) + "</td>";
					output += '<td class="text-center" style="padding-top:4px;padding-bottom:4px;">'+
					'<div class="btn-group btn-group-xs">'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return mtrouter_view_manage(\'delete\', \'' + counter + '\');"><i class="fa fa-trash"></i></a>'+
					'</div>'+
					'</td>';
					output += "</tr>";
					MTRouter_Dict[counter] = v;
					counter += 1;
				});
				$("#table_result").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	mtrouter_view_list();
	window.mtrouter_view_manage = function(act, counter){
		if(act === "delete"){
			var data = MTRouter_Dict[counter];
			var result = confirm("Do you want to delete?");
			if (result) {
				var urlto = $("input[name=urlto]").val();
			    $.ajax({
					type: "POST",
					url: urlto,
					data: {s:"delete", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, order: data.order},
					cache: false,
					dataType: "json",
					success: function(data){
						mtrouter_view_list();
					},
					error: function(jqXHR, textStatus, errorThrown){
		                //alert(errorThrown);
		            }
				});
			}
		}
	}
	$("#add_mtrouter_form").submit(function(event){
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
				mtrouter_view_list();
				$("#add_mtrouter_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
                location.reload();
            }
		});
	});
	$('.selectpicker').selectpicker({
		style: 'btn-info',
		size: 4
	});
});