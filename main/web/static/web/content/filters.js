(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var FILTERS_DICT = {};
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
                var datalist = data["filters"];
                var output = $.map(datalist, function(val, i){
                    var html = "";
                    html += `<tr>
                        <td>${i+1}</td>
                        <td>${val.fid}</td>
                        <td>${val.type}</td>
                        <td>${val.routes}</td>
                        <td>${htmlEscape(val.description)}</td>
                        <td class="text-center" style="padding-top:4px;padding-bottom:4px;">
                            <div class="btn-group btn-group-sm">
                                <a href="javascript:void(0)" class="btn btn-light" onclick="return collection_manage('delete', '${i+1}');"><i class="fas fa-trash"></i></a>
                            </div>
                        </td>
                    </tr>`;
                    FILTERS_DICT[i+1] = val;
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
                    var data = FILTERS_DICT[index];
                    $.ajax({
                    	type: "POST",
                    	url: local_path + 'manage/',
                    	data: {
                    		csrfmiddlewaretoken: csrfmiddlewaretoken,
                    		s: cmd,
                    		fid: data.fid,
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
    $(add_modal_form).on("submit", function(e){
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
    $("li.nav-item.filters-menu").addClass("active");
    $("#filter_type").on("change", function(e){
        var val = $(this).val();
        if (['transparentfilter'].includes(val)) {
            $("#filter_routes").hide();
        } else {
            $("#filter_routes").show();
            switch (val) {
                case "connectorfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="smpp-01" required>
                        <span class="text-muted"><b>cid</b> of the connector to match</span>
                    `);
                    break;
                case "userfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="bobo" required>
                        <span class="text-muted"><b>uid</b> of the user to match</span>
                    `);
                    break;
                case "groupfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="partners" required>
                        <span class="text-muted"><b>gid</b> of the group to match</span>
                    `);
                    break;
                case "sourceaddrfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="^20d+" required>
                        <span class="text-muted"><b>source_addr</b> Regular expression to match source address</span>
                    `);
                    break;
                case "destinationaddrfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="^85111$" required>
                        <span class="text-muted"><b>destination_addr</b> Regular expression to match destination address</span>
                    `);
                    break;
                case "shortmessagefilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="^hello.*$" required>
                        <span class="text-muted"><b>short_message</b> Regular expression to match message content</span>
                    `);
                    break;
                case "dateintervalfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="2014-09-18;2014-09-28" required>
                        <span class="text-muted"><b>dateInterval</b> Two dates separated by ; (date format is YYYY-MM-DD)</span>
                    `);
                    break;
                case "timeintervalfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="08:00:00;18:00:00" required>
                        <span class="text-muted"><b>timeInterval</b> Two timestamps separated by ; (timestamp format is HH:MM:SS)</span>
                    `);
                    break;
                case "tagfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="32401" required>
                        <span class="text-muted"><b>tag</b> numeric tag to match in message</span>
                    `);
                    break;
                case "evalpyfilter":
                    $("#filter_routes_inputs").html(`
                        <input type="text" name="parameter" class="form-control" placeholder="/root/thirdparty.py" required>
                        <span class="text-muted"><b>pyCode</b> Path to a python script, (<a href="https://docs.jasminsms.com/en/latest/management/jcli/modules.html#external-buslogig-filters" target="_blank">External business logic</a> for more details)</span>
                    `);
                    break;
                default:
                    $("#filter_routes_inputs").html('');
                    break;
            }
        }
    }).trigger("change");
})(jQuery);