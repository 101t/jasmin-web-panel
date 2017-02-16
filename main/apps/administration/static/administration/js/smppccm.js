$(function(){
	window.SMPPCCM_List = [];
	window.SMPPCCM_Dict = {};
	window.smppccm_view_list = function(){
		var urlto = $("input[name=urlto]").val();
		$.ajax({
			type: "POST",
			url: urlto,
			data: {s:"list", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value},
			cache: false,
			dataType: "json",
			success: function(data){
				//console.log(JSON.stringify(data));
				var connectors = data["connectors"];
				var output = "";
				var counter = 1;
				$.each(connectors, function(i, v){
					output += "<tr>";
					output += "<td>" + counter + "</td>";
					output += "<td>" + v["cid"] + "</td>";
					output += "<td>" + v["host"] + "</td>";
					output += "<td>" + v["port"] + "</td>";
					output += "<td>" + v["username"] + "</td>";
					output += "<td>" + v["password"] + "</td>";
					output += '<td class="text-center">' +( v["status"] === "started"?'<i class="fa fa-circle fa-lg text-success"><i/>':'<i class="fa fa-circle fa-lg text-default"><i/>') + "</td>";
					output += '<td class="text-center" style="padding-top:4px;padding-bottom:4px;">'+
					'<div class="btn-group btn-group-xs">'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return smppccm_view_manage(\'service\', \'' + counter + '\');"><i class="fa fa-play-circle"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return smppccm_view_manage(\'edit\', \'' + counter + '\');"><i class="fa fa-edit"></i></a>'+
					'<a href="javascript:void(0)" class="btn btn-default btn-condensed" onclick="return smppccm_view_manage(\'delete\', \'' + counter + '\');"><i class="fa fa-trash"></i></a>'+
					'</div>'+
					'</td>';
					output += "</tr>";
					SMPPCCM_List.push(counter);
					SMPPCCM_Dict[counter] = v;
					counter += 1;
				});
				$("#table_result").html(output);
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
            }
		});
	}
	window.smppccm_view_manage = function(act, counter){
		if(act === "edit"){
			var data = SMPPCCM_Dict[counter];
			$("#edit_smppccm_modal input[name=cid]").val(data.cid);
			$("#edit_smppccm_modal input[name=logfile]").val(data.logfile);
			$("#edit_smppccm_modal input[name=logrotate]").val(data.logrotate);
			$("#edit_smppccm_modal input[name=loglevel]").val(data.loglevel);
			$("#edit_smppccm_modal input[name=host]").val(data.host);
			$("#edit_smppccm_modal input[name=port]").val(data.port);
			$("#edit_smppccm_modal input[name=ssl]").val(data.ssl);
			$("#edit_smppccm_modal input[name=username]").val(data.username);
			$("#edit_smppccm_modal input[name=password]").val(data.password);
			$("#edit_smppccm_modal select[name=bind]").val(data.bind);
			$("#edit_smppccm_modal input[name=bind_to]").val(data.bind_to);
			$("#edit_smppccm_modal input[name=trx_to]").val(data.trx_to);
			$("#edit_smppccm_modal input[name=res_to]").val(data.res_to);
			$("#edit_smppccm_modal input[name=pdu_red_to]").val(data.pdu_red_to);
			$("#edit_smppccm_modal select[name=con_loss_retry]").val(data.con_loss_retry);
			$("#edit_smppccm_modal input[name=con_loss_delay]").val(data.con_loss_delay);
			$("#edit_smppccm_modal select[name=con_fail_retry]").val(data.con_fail_retry);
			$("#edit_smppccm_modal input[name=con_fail_delay]").val(data.con_fail_delay);
			$("#edit_smppccm_modal input[name=src_addr]").val(data.src_addr);
			$("#edit_smppccm_modal input[name=src_ton]").val(data.src_ton);
			$("#edit_smppccm_modal input[name=src_npi]").val(data.src_npi);
			$("#edit_smppccm_modal input[name=dst_ton]").val(data.dst_ton);
			$("#edit_smppccm_modal input[name=dst_npi]").val(data.dst_npi);
			$("#edit_smppccm_modal input[name=bind_ton]").val(data.bind_ton);
			$("#edit_smppccm_modal input[name=bind_npi]").val(data.bind_npi);
			$("#edit_smppccm_modal input[name=validity]").val(data.validity);
			$("#edit_smppccm_modal input[name=priority]").val(data.priority);
			$("#edit_smppccm_modal input[name=requeue_delay]").val(data.requeue_delay);
			$("#edit_smppccm_modal input[name=addr_range]").val(data.addr_range);
			$("#edit_smppccm_modal input[name=systype]").val(data.systype);
			$("#edit_smppccm_modal input[name=dlr_expiry]").val(data.dlr_expiry);
			$("#edit_smppccm_modal input[name=submit_throughput]").val(data.submit_throughput);
			$("#edit_smppccm_modal input[name=proto_id]").val(data.proto_id);
			$("#edit_smppccm_modal input[name=coding]").val(data.coding);
			$("#edit_smppccm_modal input[name=elink_interval]").val(data.elink_interval);
			$("#edit_smppccm_modal input[name=def_msg_id]").val(data.def_msg_id);
			$("#edit_smppccm_modal input[name=ripf]").val(data.ripf);
			$("#edit_smppccm_modal input[name=dlr_msgid]").val(data.dlr_msgid);
			$("#edit_smppccm_modal").modal('show');
		}else if(act === "delete"){
			var data = SMPPCCM_Dict[counter];
			var result = confirm("Want to delete?");
			if (result) {
				var urlto = $("input[name=urlto]").val();
			    $.ajax({
					type: "POST",
					url: urlto,
					data: {s:"delete", csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, cid: data.cid},
					cache: false,
					dataType: "json",
					success: function(data){
						smppccm_view_list();
					},
					error: function(jqXHR, textStatus, errorThrown){
		                //alert(errorThrown);
		            }
				});
			}
		}else if(act === "service"){
			var data = SMPPCCM_Dict[counter];
			$("#service_smppccm_modal input[name=cid]").val(data.cid);
			$("#service_smppccm_modal").modal('show');
		}
	}
	smppccm_view_list();
	$("#add_smppccm_form").submit(function(event){
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
				smppccm_view_list();
				$("#add_smppccm_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
	$("#edit_smppccm_form").submit(function(event){
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
				smppccm_view_list();
				$("#edit_smppccm_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
	$("#service_smppccm_form").submit(function(event){
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
				smppccm_view_list();
				$("#service_smppccm_modal").modal("hide");
			},
			error: function(jqXHR, textStatus, errorThrown){
                //alert(errorThrown);
                $inputs.prop("disabled", false);
            }
		});
	});
});