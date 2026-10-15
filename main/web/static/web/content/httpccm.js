(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var HTTPCCM_DICT = {};
    var COLUMNS = 5;
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
                var datalist = data["connectors"];
                HTTPCCM_DICT = {};
                var output = $.map(datalist, function(val, i){
                    HTTPCCM_DICT[i+1] = val;
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.cid) + '</td>' +
                        '<td class="text-break"><code>' + escapeHtml(val.url) + '</code></td>' +
                        '<td><span class="badge badge-info">' + escapeHtml(val.method) + '</span></td>' +
                        '<td class="text-center" style="padding-top:4px;padding-bottom:4px;"><div class="btn-group btn-group-sm">' +
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
        } else if (cmd == "delete") {
            var connector = HTTPCCM_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, cid: connector.cid}, collectionlist_check);
            });
        }
    };
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form).on("submit", function(e){
        e.preventDefault();
        submitAjaxForm(this, collectionlist_check);
    });
    $("li.nav-item.httpccm-menu").addClass("active");
})(jQuery);
