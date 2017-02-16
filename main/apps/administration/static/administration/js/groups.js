$(function(){
	window.Groups_List = [];
	window.Groups_Dict = {};
	window.groups_view_list = function(){
		var urlto = $("input[name=urlto]").val();
		$.ajax({
			type: "POST",
			url: urlto,
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var groups = data["groups"];
				var output = "";
				var counter = 1;
				$.each(groups, function(i, v){
					output += "<tr>";
					output += "<td>" + counter + "</td>";
					output += "<td>" + v["name"] + "</td>";
					output += '<td class="text-center">' +( v["status"] === "enabled"?'<i class="fa fa-circle fa-lg text-success"><i/>':'<i class="fa fa-circle fa-lg text-default"><i/>') + "</td>";
					output += '<td class="text-center" style="padding-top:4px;padding-bottom:4px;">'+
					'<div class="btn-group btn-group-xs">'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return groups_view_manage(\'service\', \'' + counter + '\');"><i class="fa fa-play-circle"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return groups_view_manage(\'edit\', \'' + counter + '\');"><i class="fa fa-edit"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return groups_view_manage(\'delete\', \'' + counter + '\');"><i class="fa fa-trash"></i></a>'+
					'</div>'+
					'</td>';
					output += "</tr>";
					Groups_List.push(counter);
					Groups_Dict[counter] = v;
					counter += 1;
				});
				$("#table_result").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	window.groups_view_manage = function(act, counter){
		if(act === "edit"){
			var data = Groups_Dict[counter];
			$("#edit_groups_modal input[name=gid]").val(data.name);
			$("#edit_groups_modal").modal('show');
		}else if(act === "delete"){
			var data = Groups_Dict[counter];
			var result = confirm("Do you want to delete?");
			if (result) {
				var urlto = $("input[name=urlto]").val();
			    $.ajax({
					type: "POST",
					url: urlto,
					data: {s:"delete", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, gid: data.name},
					cache: false,
					dataType: "json",
					success: function(data){
						groups_view_list();
					},
					error: function(jqXHR, textStatus, errorThrown){
		                //alert(errorThrown);
		            }
				});
			}
		}else if(act === "service"){
			var data = Groups_Dict[counter];
			$("#service_groups_modal input[name=gid]").val(data.name);
			$("#service_groups_modal").modal('show');
		}
	}
	groups_view_list();
	$("#add_groups_form").submit(function(event){
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
				groups_view_list();
				$("#add_groups_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
                location.reload();
            }
		});
	});
	$("#edit_groups_form").submit(function(event){
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
				groups_view_list();
				$("#edit_groups_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
	$("#service_groups_form").submit(function(event){
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
				groups_view_list();
				$("#service_groups_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
});