(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var USERS_DICT = {}, GROUPS_DICT = {};
    var collectionlist_check = function(){
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",

            },
            dataType: "json",
            success: function(data){
                var datalist = data["users"];
                var output = $.map(datalist, function(val, i){
                    var html = "";
                    html += `<tr>
                        <td>${i+1}</td>
                        <td>${val.uid}</td>
                        <td>${val.gid}</td>
                        <td>${val.username}</td>
                        <td class="text-center">${val.status === "enabled"?'<i class="fas fa-circle fa-lg text-success"><i/>':'<i class="fas fa-circle fa-lg text-default"><i/>'}</td>
                        <td>${val.mt_messaging_cred.quota.balance}</td>
                        <td>${val.mt_messaging_cred.quota.sms_count}</td>
                        <td class="text-center" style="padding-top:4px;padding-bottom:4px;">
                            <div class="btn-group btn-group-sm">
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('service', '${i+1}');"><i class="fas fa-play-circle"></i></a>
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('edit', '${i+1}');"><i class="fas fa-edit"></i></a>
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('delete', '${i+1}');"><i class="fas fa-trash"></i></a>
                            </div>
                        </td>
                    </tr>`;
                    USERS_DICT[i+1] = val;
                    return html;
                });
                $("#collectionlist").html(datalist.length > 0 ? output : $(".isEmpty").html());
            }, error: function(jqXHR, textStatus, errorThrown){quick_display_modal_error(jqXHR.responseText);}
        });
    }
    collectionlist_check();
    window.collection_manage = function(cmd, index){
        index = index || -1;
        if (cmd == "add") {
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "edit") {
            var data = USERS_DICT[index];
            $(edit_modal_form+" input[name=username]").val(data.username);
            $(edit_modal_form+" input[name=password]").val(data.password);
            $(edit_modal_form+" select[name=gid]").val(data.gid);
            $(edit_modal_form+" input[name=uid]").val(data.uid);
            $(edit_modal_form+" input[name=balance]").val(data.mt_messaging_cred.quota.balance);
            $(edit_modal_form+" input[name=sms_count]").val(data.mt_messaging_cred.quota.sms_count);
            $(edit_modal_form+" input[name=early_percent]").val(data.mt_messaging_cred.quota.early_percent);
            $(edit_modal_form+" input[name=http_throughput]").val(data.mt_messaging_cred.quota.http_throughput);
            $(edit_modal_form+" input[name=smpps_throughput]").val(data.mt_messaging_cred.quota.smpps_throughput);
            $(edit_modal_form+" input[name=http_send]")[0].checked = data.mt_messaging_cred.authorization.http_send === "True"? true : false;
            $(edit_modal_form+" input[name=http_balance]")[0].checked = data.mt_messaging_cred.authorization.http_balance === "True"? true : false;
            $(edit_modal_form+" input[name=http_rate]")[0].checked = data.mt_messaging_cred.authorization.http_rate === "True"? true : false;
            $(edit_modal_form+" input[name=http_bulk]")[0].checked = data.mt_messaging_cred.authorization.http_bulk === "True"? true : false;
            $(edit_modal_form+" input[name=smpps_send]")[0].checked = data.mt_messaging_cred.authorization.smpps_send === "True"? true : false;
            $(edit_modal_form+" input[name=http_long_content]")[0].checked = data.mt_messaging_cred.authorization.http_long_content === "True"? true : false;
            $(edit_modal_form+" input[name=dlr_level]")[0].checked = data.mt_messaging_cred.authorization.dlr_level === "True"? true : false;
            $(edit_modal_form+" input[name=http_dlr_method]")[0].checked = data.mt_messaging_cred.authorization.http_dlr_method === "True"? true : false;
            $(edit_modal_form+" input[name=src_addr]")[0].checked = data.mt_messaging_cred.authorization.src_addr === "True"? true : false;
            $(edit_modal_form+" input[name=priority]")[0].checked = data.mt_messaging_cred.authorization.priority === "True"? true : false;
            $(edit_modal_form+" input[name=validity_period]")[0].checked = data.mt_messaging_cred.authorization.validity_period === "True"? true : false;
            $(edit_modal_form+" input[name=src_addr_f]").val(data.mt_messaging_cred.valuefilter.src_addr);
            $(edit_modal_form+" input[name=dst_addr_f]").val(data.mt_messaging_cred.valuefilter.dst_addr);
            $(edit_modal_form+" input[name=content_f]").val(data.mt_messaging_cred.valuefilter.content);
            $(edit_modal_form+" input[name=priority_f]").val(data.mt_messaging_cred.valuefilter.priority);
            $(edit_modal_form+" input[name=validity_period_f]").val(data.mt_messaging_cred.valuefilter.validity_period);
            $(edit_modal_form+" input[name=src_addr_d]").val(data.mt_messaging_cred.defaultvalue.src_addr);
            showThisBox(variant_boxes, edit_modal_form);
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
                    var data = USERS_DICT[index];
                    $.ajax({
                    	type: "POST",
                    	url: local_path + 'manage/',
                    	data: {
                    		csrfmiddlewaretoken: csrfmiddlewaretoken,
                    		s: cmd,
                    		uid: data.uid,
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
        } else if (cmd == "service") {
            var data = USERS_DICT[index];
            $(service_modal_form+" input[name=uid]").val(data.uid);
            showThisBox(variant_boxes, service_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "groups") {
            $.ajax({
                url: main_trans.url2groups,
                type: "POST",
                data: {
                    csrfmiddlewaretoken,
                    s: "list",
                },
                dataType: "json",
                success: function(data){
                    var datalist = data["groups"];
                    var html = $.map(datalist, function(val, i){
                        GROUPS_DICT[i+1] = val;
                        return `<option>${val.name}</option>`;
                    });
                    $(add_modal_form+" select[name=gid]").html(html);
                    $(edit_modal_form+" select[name=gid]").html(html);
                }
            })
        }
    }
    collection_manage("groups");
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
    $("li.nav-item.users-menu").addClass("active");
})(jQuery);