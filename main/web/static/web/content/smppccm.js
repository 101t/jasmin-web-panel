(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var SMPPCCM_DICT = {};
    var collectionlist_check = function() {
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",

            },
            dataType: "json",
            success: function(data){
                var datalist = data["connectors"];
                var output = $.map(datalist, function(val, i){
                    var html = "";
                    html += `<tr>
                        <td>${i+1}</td>
                        <td>${val.cid}</td>
                        <td>${val.host}</td>
                        <td>${val.port}</td>
                        <td>${val.username}</td>
                        <td>${val.password}</td>
                        <td class="text-center">${val.status === "started"?'<i class="fas fa-circle fa-lg text-success"><i/>':'<i class="fas fa-circle fa-lg text-default"><i/>'}</td>
                        <td class="text-center" style="padding-top:4px;padding-bottom:4px;">
                            <div class="btn-group btn-group-sm">
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('service', '${i+1}');"><i class="fas fa-play-circle"></i></a>
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('edit', '${i+1}');"><i class="fas fa-edit"></i></a>
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('delete', '${i+1}');"><i class="fas fa-trash"></i></a>
                            </div>
                        </td>
                    </tr>`;
                    SMPPCCM_DICT[i+1] = val;
                    return html;
                });
                $("#collectionlist").html(datalist.length > 0 ? output : $(".isEmpty").html());
            }, error: function(jqXHR, textStatus, errorThrown){quick_display_modal_error(jqXHR.responseText);}
        })
    }
    collectionlist_check();
    window.collection_manage = function(cmd, index){
        index = index || -1;
        if (cmd == "add") {
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "edit") {
            showThisBox(variant_boxes, edit_modal_form);
            var data = SMPPCCM_DICT[index];
            $(edit_modal_form+" input[name=cid]").val(data.cid);
            $(edit_modal_form+" input[name=logfile]").val(data.logfile);
            $(edit_modal_form+" input[name=logrotate]").val(data.logrotate);
            $(edit_modal_form+" input[name=loglevel]").val(data.loglevel);
            $(edit_modal_form+" input[name=host]").val(data.host);
            $(edit_modal_form+" input[name=port]").val(data.port);
            $(edit_modal_form+" input[name=ssl]").val(data.ssl);
            $(edit_modal_form+" input[name=username]").val(data.username);
            $(edit_modal_form+" input[name=password]").val(data.password);
            $(edit_modal_form+" select[name=bind]").val(data.bind);
            $(edit_modal_form+" input[name=bind_to]").val(data.bind_to);
            $(edit_modal_form+" input[name=trx_to]").val(data.trx_to);
            $(edit_modal_form+" input[name=res_to]").val(data.res_to);
            $(edit_modal_form+" input[name=pdu_red_to]").val(data.pdu_red_to);
            $(edit_modal_form+" select[name=con_loss_retry]").val(data.con_loss_retry);
            $(edit_modal_form+" input[name=con_loss_delay]").val(data.con_loss_delay);
            $(edit_modal_form+" select[name=con_fail_retry]").val(data.con_fail_retry);
            $(edit_modal_form+" input[name=con_fail_delay]").val(data.con_fail_delay);
            $(edit_modal_form+" input[name=src_addr]").val(data.src_addr);
            $(edit_modal_form+" input[name=src_ton]").val(data.src_ton);
            $(edit_modal_form+" input[name=src_npi]").val(data.src_npi);
            $(edit_modal_form+" input[name=dst_ton]").val(data.dst_ton);
            $(edit_modal_form+" input[name=dst_npi]").val(data.dst_npi);
            $(edit_modal_form+" input[name=bind_ton]").val(data.bind_ton);
            $(edit_modal_form+" input[name=bind_npi]").val(data.bind_npi);
            $(edit_modal_form+" input[name=validity]").val(data.validity);
            $(edit_modal_form+" input[name=priority]").val(data.priority);
            $(edit_modal_form+" input[name=requeue_delay]").val(data.requeue_delay);
            $(edit_modal_form+" input[name=addr_range]").val(data.addr_range);
            $(edit_modal_form+" input[name=systype]").val(data.systype);
            $(edit_modal_form+" input[name=dlr_expiry]").val(data.dlr_expiry);
            $(edit_modal_form+" input[name=submit_throughput]").val(data.submit_throughput);
            $(edit_modal_form+" input[name=proto_id]").val(data.proto_id);
            $(edit_modal_form+" input[name=coding]").val(data.coding);
            $(edit_modal_form+" input[name=elink_interval]").val(data.elink_interval);
            $(edit_modal_form+" input[name=def_msg_id]").val(data.def_msg_id);
            $(edit_modal_form+" input[name=ripf]").val(data.ripf);
            $(edit_modal_form+" input[name=dlr_msgid]").val(data.dlr_msgid);
            $("#collection_modal").modal("show");
        } else if (cmd == "service") {
            showThisBox(variant_boxes, service_modal_form);
            var data = SMPPCCM_DICT[index];
            $(service_modal_form+" input[name=cid]").val(data.cid);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            sweetAlert({
                title: global_trans["areyousuretodelete"],
                text: global_trans["youwontabletorevertthis"],
                type: 'warning',
                showCancelButton: true,
                cancelButtonClass: "btn btn-secondary m-btn m-btn--pill m-btn--icon",
                cancelButtonText: global_trans["no"],
                confirmButtonClass: "btn btn-danger m-btn m-btn--pill m-btn--air m-btn--icon",
                confirmButtonText: global_trans["yes"],
            }, function(isConfirm){
                if (isConfirm) {
                    var data = SMPPCCM_DICT[index];
                    $.ajax({
                    	type: "POST",
                    	url: local_path + 'manage/',
                    	data: {
                    		csrfmiddlewaretoken: csrfmiddlewaretoken,
                    		s: cmd,
                    		cid: data.cid,
                    	},
                    	beforeSend: function(){},
						success: function(data){
							toastr.success(data["message"], {closeButton: true, progressBar: true,});
							collectionlist_check();
						},
						error: function(jqXHR, textStatus, errorThrown){
							toastr.error(JSON.parse(jqXHR.responseText)["message"], {closeButton: true, progressBar: true,});
						}
                    })
                }
            });
        }
    }
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form+","+edit_modal_form+","+service_modal_form).on("submit", function(e){
        e.preventDefault();
        var serializeform = $(this).serialize();
		var inputs = $(this).find("input, select, button, textarea");
		//inputs.prop("disabled", true);
		$.ajax({
			type: "POST",
			url: $(this).attr("action"),
			data: serializeform,
			beforeSend: function(){inputs.prop("disabled", true);},
			success: function(data){
				toastr.success(data["message"], {closeButton: true, progressBar: true,});
				inputs.prop("disabled", false);
				$(".modal").modal("hide");
				collectionlist_check();
				//setTimeout(location.reload.bind(location), 2000);
			},
			error: function(jqXHR, textStatus, errorThrown){
				inputs.prop("disabled", false);
				toastr.error(JSON.parse(jqXHR.responseText)["message"], {closeButton: true, progressBar: true,});
			}
		});
    });
    $("li.nav-item.smppccm-menu").addClass("active");
})(jQuery);