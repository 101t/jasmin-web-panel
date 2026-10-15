(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var GROUPS_DICT = {};
    var COLUMNS = 4;
    var collectionlist_check = function(){
        tableLoading("#collectionlist", COLUMNS);
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",
            },
            dataType: "json",
            success: function(data){
                var datalist = data["groups"];
                GROUPS_DICT = {};
                var output = $.map(datalist, function(val, i){
                    GROUPS_DICT[i+1] = val;
                    var status = val.status === "enabled"
                        ? '<span class="badge badge-success">' + escapeHtml(main_trans.enabled) + '</span>'
                        : '<span class="badge badge-secondary">' + escapeHtml(main_trans.disabled) + '</span>';
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.name) + '</td>' +
                        '<td class="text-center">' + status + '</td>' +
                        '<td class="text-center" style="padding-top:4px;padding-bottom:4px;"><div class="btn-group btn-group-sm">' +
                            '<button type="button" class="btn btn-light" title="' + escapeHtml(main_trans.service) + '" aria-label="' + escapeHtml(main_trans.service) + '" onclick="return collection_manage(\'service\', ' + (i+1) + ');"><i class="fas fa-play-circle"></i></button>' +
                            '<button type="button" class="btn btn-light" title="' + escapeHtml(main_trans.delete) + '" aria-label="' + escapeHtml(main_trans.delete) + '" onclick="return collection_manage(\'delete\', ' + (i+1) + ');"><i class="fas fa-trash"></i></button>' +
                        '</div></td>' +
                    '</tr>';
                });
                $("#collectionlist").html(datalist.length > 0 ? output.join('') : $(".isEmpty").html());
            },
            error: function(jqXHR){ tableError("#collectionlist", COLUMNS, jqXHR, collectionlist_check); }
        });
    };
    collectionlist_check();
    window.collection_manage = function(cmd, index){
        index = index || -1;
        if (cmd == "add") {
            $(add_modal_form)[0].reset();
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "service") {
            var data = GROUPS_DICT[index];
            $(service_modal_form+" input[name=gid]").val(data.name);
            $(service_modal_form+" select[name=s]").val(data.status === "enabled" ? "disable" : "enable");
            showThisBox(variant_boxes, service_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            var group = GROUPS_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, gid: group.name}, collectionlist_check);
            });
        }
    };
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form+","+service_modal_form).on("submit", function(e){
        e.preventDefault();
        submitAjaxForm(this, collectionlist_check);
    });
    $("li.nav-item.groups-menu").addClass("active");
})(jQuery);
