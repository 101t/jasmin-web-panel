$(function(){
	window.Groups_Dict = {};
	window.load_groups_in_select = function(){
		var urltogroups = $("input[name=urltogroups]").val();
		$.ajax({
			url: urltogroups,
			type: "POST",
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var groups = data["groups"];
				var output = "";
				var counter = 1;
				$.each(groups, function(i, v){
					output += "<option>" + v.name + "</option>";
					Groups_Dict[counter] = v;
					counter += 1;
				});
				$("#gid_select").html(output);
				$("#gid_select_edit").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	load_groups_in_select();
	window.Users_Dict = {};
	window.users_view_list = function(){
		var urlto = $("input[name=urlto]").val();
		$.ajax({
			type: "POST",
			url: urlto,
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				var users = data["users"];
				//console.log(JSON.stringify(data));
				var output = "";
				var counter = 1;
				$.each(users, function(i, v){
					output += "<tr>";
					output += "<td>" + counter + "</td>";
					output += "<td>" + v["uid"] + "</td>";
					output += "<td>" + v["gid"] + "</td>";
					output += "<td>" + v["username"] + "</td>";
					output += '<td class="text-center">' +( v["status"] === "enabled"?'<i class="fa fa-circle fa-lg text-success"><i/>':'<i class="fa fa-circle fa-lg text-default"><i/>') + "</td>";
					output += "<td>" + v["mt_messaging_cred"]["quota"]["balance"] + "</td>";
					output += "<td>" + v["mt_messaging_cred"]["quota"]["sms_count"] + "</td>";
					output += '<td class="text-center" style="padding-top:4px;padding-bottom:4px;">'+
					'<div class="btn-group btn-group-xs">'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return users_view_manage(\'service\', \'' + counter + '\');"><i class="fa fa-play-circle"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return users_view_manage(\'edit\', \'' + counter + '\');"><i class="fa fa-edit"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return users_view_manage(\'delete\', \'' + counter + '\');"><i class="fa fa-trash"></i></a>'+
					'</div>'+
					'</td>';
					output += "</tr>";
					Users_Dict[counter] = v;
					counter += 1;
				});
				$("#table_result").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	users_view_list();
	$("#add_users_form").submit(function(event){
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
				users_view_list();
				$("#add_users_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
                location.reload();
            }
		});
	});
	window.users_view_manage = function(act, counter){
		if(act === "edit"){
			var data = Users_Dict[counter];
			$("#edit_users_modal input[name=username]").val(data.username);
			$("#edit_users_modal input[name=password]").val(data.password);
			$("#edit_users_modal select[name=gid]").val(data.gid);
			$("#edit_users_modal input[name=uid]").val(data.uid);
			$("#edit_users_modal input[name=balance]").val(data.mt_messaging_cred.quota.balance);
			$("#edit_users_modal input[name=sms_count]").val(data.mt_messaging_cred.quota.sms_count);
			$("#edit_users_modal input[name=early_percent]").val(data.mt_messaging_cred.quota.early_percent);
			$("#edit_users_modal input[name=http_throughput]").val(data.mt_messaging_cred.quota.http_throughput);
			$("#edit_users_modal input[name=smpps_throughput]").val(data.mt_messaging_cred.quota.smpps_throughput);
			$("#edit_users_modal input[name=http_send]")[0].checked = data.mt_messaging_cred.authorization.http_send === "True"? true : false;
			$("#edit_users_modal input[name=http_balance]")[0].checked = data.mt_messaging_cred.authorization.http_balance === "True"? true : false;
			$("#edit_users_modal input[name=http_rate]")[0].checked = data.mt_messaging_cred.authorization.http_rate === "True"? true : false;
			$("#edit_users_modal input[name=http_bulk]")[0].checked = data.mt_messaging_cred.authorization.http_bulk === "True"? true : false;
			$("#edit_users_modal input[name=smpps_send]")[0].checked = data.mt_messaging_cred.authorization.smpps_send === "True"? true : false;
			$("#edit_users_modal input[name=http_long_content]")[0].checked = data.mt_messaging_cred.authorization.http_long_content === "True"? true : false;
			$("#edit_users_modal input[name=dlr_level]")[0].checked = data.mt_messaging_cred.authorization.dlr_level === "True"? true : false;
			$("#edit_users_modal input[name=http_dlr_method]")[0].checked = data.mt_messaging_cred.authorization.http_dlr_method === "True"? true : false;
			$("#edit_users_modal input[name=src_addr]")[0].checked = data.mt_messaging_cred.authorization.src_addr === "True"? true : false;
			$("#edit_users_modal input[name=priority]")[0].checked = data.mt_messaging_cred.authorization.priority === "True"? true : false;
			$("#edit_users_modal input[name=validity_period]")[0].checked = data.mt_messaging_cred.authorization.validity_period === "True"? true : false;
			$("#edit_users_modal input[name=src_addr_f]").val(data.mt_messaging_cred.valuefilter.src_addr);
			$("#edit_users_modal input[name=dst_addr_f]").val(data.mt_messaging_cred.valuefilter.dst_addr);
			$("#edit_users_modal input[name=content_f]").val(data.mt_messaging_cred.valuefilter.content);
			$("#edit_users_modal input[name=priority_f]").val(data.mt_messaging_cred.valuefilter.priority);
			$("#edit_users_modal input[name=validity_period_f]").val(data.mt_messaging_cred.valuefilter.validity_period);
			$("#edit_users_modal input[name=src_addr_d]").val(data.mt_messaging_cred.defaultvalue.src_addr);
			$("#edit_users_modal").modal('show');
		}else if(act === "delete"){
			var data = Users_Dict[counter];
			var result = confirm("Want to delete?");
			if (result) {
				var urlto = $("input[name=urlto]").val();
			    $.ajax({
					type: "POST",
					url: urlto,
					data: {s:"delete", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, uid: data.uid},
					cache: false,
					dataType: "json",
					success: function(data){
						users_view_list();
					},
					error: function(jqXHR, textStatus, errorThrown){
		                //alert(errorThrown);
		            }
				});
			}
		}else if(act === "service"){
			var data = Users_Dict[counter];
			$("#service_users_modal input[name=uid]").val(data.uid);
			$("#service_users_modal").modal('show');
		}
	}
	$("#edit_users_form").submit(function(event){
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
				users_view_list();
				$("#edit_users_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
	$("#service_users_form").submit(function(event){
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
				users_view_list();
				$("#service_users_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
});